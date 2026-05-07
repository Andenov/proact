"""
Forecast horizon service.

Computes risk scores for 4 time windows per district:
  current  — today (last 30d actual data)
  7d       — next 7 days  (uses Open-Meteo forecast already in DB)
  14d      — next 14 days (uses Open-Meteo 16-day forecast)
  30d      — 30-day outlook (16-day forecast + climatological fill)

Beyond the available forecast window, daily rainfall is filled with the
30-year monthly climatological average from NASA POWER.
"""

import json
import logging
from datetime import date, timedelta
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.district import District
from app.models.hazard import HazardStaticFeature
from app.models.weather import WeatherObservation
from app.services.risk_engine import (
    compute_flood_score,
    compute_food_stress_score,
    compute_landslide_score,
)
from app.services.weather_service import compute_rolling_stats

logger = logging.getLogger(__name__)

_HORIZONS = [
    {"key": "current", "days": 0,  "label": "Today"},
    {"key": "7d",      "days": 7,  "label": "Next 7 days"},
    {"key": "14d",     "days": 14, "label": "Next 14 days"},
    {"key": "30d",     "days": 30, "label": "30-day outlook"},
]


def _obs_to_dict(o: WeatherObservation) -> Dict:
    return {
        "date": str(o.date),
        "rainfall_mm": o.rainfall_mm or 0.0,
        "tmax_c": o.tmax_c,
        "tmin_c": o.tmin_c,
        "soil_moisture": o.soil_moisture,
    }


def _clim_daily(monthly_baseline: Optional[List[float]], month: int) -> float:
    if monthly_baseline and len(monthly_baseline) == 12:
        return monthly_baseline[month - 1]
    return 4.0  # fallback: ~120 mm/month for Uganda


def _build_window(
    obs_by_date: Dict[str, Dict],
    window_start: date,
    window_end: date,
    monthly_baseline: Optional[List[float]],
    today: date,
) -> List[Dict]:
    """
    Build a 30-day observation window ending on window_end.
    Future dates not in obs_by_date are filled with climatological daily average.
    """
    days = (window_end - window_start).days + 1
    window: List[Dict] = []
    for i in range(days):
        d = window_start + timedelta(days=i)
        d_str = d.isoformat()
        if d_str in obs_by_date:
            window.append(obs_by_date[d_str])
        elif d > today:
            # Fill with climatological average
            window.append({
                "date": d_str,
                "rainfall_mm": _clim_daily(monthly_baseline, d.month),
                "tmax_c": None,
                "tmin_c": None,
                "soil_moisture": None,
            })
    return window


def _score_window(
    window: List[Dict],
    monthly_baseline: Optional[List[float]],
    floodplain: float,
    slope: float,
    landslide_baseline: float,
    target_date: date,
) -> Optional[Dict]:
    stats = compute_rolling_stats(window, monthly_baseline_mm_per_day=monthly_baseline)
    if not stats:
        return None
    sm = stats.get("soil_moisture") or 0.5
    flood = compute_flood_score(stats["rain_3d"], stats["rain_7d"], stats["anomaly_score"], floodplain)
    landslide = compute_landslide_score(stats["rain_3d"], stats["rain_7d"], slope, landslide_baseline, sm)
    food = compute_food_stress_score(stats["rain_deficit_30d"], stats["heat_stress_days"], target_date.month)
    return {
        "flood":       {"score": flood["score"],      "level": flood["level"]},
        "landslide":   {"score": landslide["score"],  "level": landslide["level"]},
        "food_stress": {"score": food["score"],       "level": food["level"]},
    }


def compute_risk_horizons(district_id: int, db: Session) -> List[Dict]:
    """
    Returns a list of risk snapshots for each horizon window.
    Each item: { key, label, target_date, note?, flood, landslide, food_stress }
    """
    district = db.query(District).filter(District.id == district_id).first()
    if not district:
        return []

    hazard = (
        db.query(HazardStaticFeature)
        .filter(HazardStaticFeature.district_id == district_id)
        .first()
    )
    floodplain        = hazard.floodplain_score        if hazard else 0.3
    slope             = hazard.slope_index             if hazard else 0.3
    landslide_base    = hazard.landslide_baseline_score if hazard else 0.2
    monthly_baseline: Optional[List[float]] = None
    if hazard and hazard.rainfall_monthly_avg_json:
        try:
            monthly_baseline = json.loads(hazard.rainfall_monthly_avg_json)
        except Exception:
            pass

    today = date.today()
    fetch_start = today - timedelta(days=35)
    fetch_end   = today + timedelta(days=30)

    obs_rows = (
        db.query(WeatherObservation)
        .filter(
            WeatherObservation.district_id == district_id,
            WeatherObservation.date >= fetch_start,
            WeatherObservation.date <= fetch_end,
        )
        .order_by(WeatherObservation.date.asc())
        .all()
    )
    obs_by_date = {str(o.date): _obs_to_dict(o) for o in obs_rows}

    results = []
    for h in _HORIZONS:
        target_date  = today + timedelta(days=h["days"])
        window_start = target_date - timedelta(days=30)
        window       = _build_window(obs_by_date, window_start, target_date, monthly_baseline, today)

        if not window:
            continue

        scores = _score_window(window, monthly_baseline, floodplain, slope, landslide_base, target_date)
        if not scores:
            continue

        entry: Dict = {
            "key":         h["key"],
            "label":       h["label"],
            "target_date": str(target_date),
            **scores,
        }
        if h["key"] == "30d":
            entry["note"] = "16-day forecast + seasonal climatology"
        results.append(entry)

    return results
