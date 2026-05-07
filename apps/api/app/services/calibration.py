"""
Weight calibration service for the PROACT risk engine.

Uses logistic regression on historical disaster events + negative samples
to learn feature weights that replace hand-tuned defaults.
"""

import asyncio
import logging
from datetime import date, timedelta
from typing import Dict, List, Optional, Tuple

_FETCH_SEMAPHORE = asyncio.Semaphore(3)  # max 3 concurrent Open-Meteo requests

import numpy as np
from sklearn.linear_model import LogisticRegression

from app.services.weather_service import fetch_weather_for_district, compute_rolling_stats
from app.services.nasa_power_service import fetch_soil_moisture, fetch_climatological_baseline

logger = logging.getLogger(__name__)

# District centroids
DISTRICT_COORDS: Dict[str, Tuple[float, float]] = {
    "Mbale":   (1.0796, 34.1754),
    "Bududa":  (1.0000, 34.3500),
    "Sironko": (1.2333, 34.2500),
    "Moroto":  (2.5340, 34.6680),
    "Kotido":  (2.9833, 34.1333),
}

# Static hazard features per district
DISTRICT_STATIC: Dict[str, Dict[str, float]] = {
    "Mbale":   {"floodplain_score": 0.65, "slope_index": 0.55, "landslide_baseline": 0.60},
    "Bududa":  {"floodplain_score": 0.45, "slope_index": 0.90, "landslide_baseline": 0.85},
    "Sironko": {"floodplain_score": 0.50, "slope_index": 0.70, "landslide_baseline": 0.65},
    "Moroto":  {"floodplain_score": 0.25, "slope_index": 0.30, "landslide_baseline": 0.20},
    "Kotido":  {"floodplain_score": 0.20, "slope_index": 0.15, "landslide_baseline": 0.15},
}

# Uganda seasonality (same as risk_engine, inlined to avoid circular import)
_SEASONALITY = {
    1: 0.8, 2: 0.9, 3: 1.0, 4: 0.9,
    5: 0.7, 6: 0.6, 7: 0.7, 8: 0.7,
    9: 0.8, 10: 1.0, 11: 0.9, 12: 0.8,
}

# Negative sample dates: known low-risk periods per hazard class
_NEGATIVE_DATES_FLOOD = [
    date(2015, 7, 10), date(2016, 6, 20), date(2017, 7, 5),
    date(2020, 7, 15), date(2021, 6, 22), date(2023, 7, 8),
]
_NEGATIVE_DATES_FOOD_STRESS = [
    date(2014, 5, 15), date(2016, 10, 20), date(2018, 5, 10),
    date(2020, 10, 15), date(2023, 5, 20), date(2023, 10, 10),
]
_FLOOD_DISTRICTS = ["Mbale", "Bududa", "Sironko"]
_FOOD_DISTRICTS  = ["Moroto", "Kotido"]


async def _fetch_stats(district: str, target_date: date) -> Optional[Dict]:
    """Fetch weather + soil moisture and compute rolling stats for one district/date."""
    coords = DISTRICT_COORDS.get(district)
    if not coords:
        logger.warning(f"Unknown district: {district}")
        return None

    lat, lon = coords
    start = target_date - timedelta(days=36)

    async with _FETCH_SEMAPHORE:
        await asyncio.sleep(0.5)  # small courtesy delay between requests
        weather = await fetch_weather_for_district(lat, lon, start, target_date)
        if not weather:
            logger.warning(f"No weather data for {district} on {target_date}")
            return None

        sm_data = await fetch_soil_moisture(lat, lon, start, target_date)
        sm_by_date = {r["date"]: r["soil_moisture"] for r in sm_data}
        for obs in weather:
            obs["soil_moisture"] = sm_by_date.get(obs["date"])

        baseline = fetch_climatological_baseline(lat, lon)

    stats = compute_rolling_stats(weather, baseline)
    if not stats:
        return None

    static = DISTRICT_STATIC.get(district, {})
    stats["floodplain_score"]    = static.get("floodplain_score", 0.5)
    stats["slope_index"]         = static.get("slope_index", 0.5)
    stats["landslide_baseline"]  = static.get("landslide_baseline", 0.5)
    stats["district"]            = district
    stats["date"]                = target_date
    return stats


def _flood_features(s: Dict) -> List[float]:
    return [
        min(s["rain_3d"] / 120, 1.0),
        min(s["rain_7d"] / 250, 1.0),
        max(min((s["anomaly_score"] + 1) / 2, 1.0), 0.0),
        max(min(s["floodplain_score"], 1.0), 0.0),
    ]


def _landslide_features(s: Dict) -> List[float]:
    sm = s.get("soil_moisture") or 0.5
    return [
        min(s["rain_3d"] / 120, 1.0),
        max(min(sm, 1.0), 0.0),
        min(s["rain_7d"] / 250, 1.0),
        max(min(s["slope_index"], 1.0), 0.0),
        max(min(s["landslide_baseline"], 1.0), 0.0),
    ]


def _food_stress_features(s: Dict) -> List[float]:
    deficit = s.get("rain_deficit_30d", 0)
    return [
        min(deficit / 100.0, 1.0) if deficit > 0 else 0.0,
        min(s.get("heat_stress_days", 0) / 15.0, 1.0),
        _SEASONALITY.get(s["date"].month, 0.8),
    ]


def _fit_weights(
    X_pos: List[List[float]],
    X_neg: List[List[float]],
    feature_names: List[str],
    hazard: str,
) -> Optional[Dict[str, float]]:
    if len(X_pos) < 2 or len(X_neg) < 2:
        logger.warning(f"{hazard}: not enough samples (pos={len(X_pos)}, neg={len(X_neg)}), skipping")
        return None

    X = np.array(X_pos + X_neg, dtype=float)
    y = np.array([1] * len(X_pos) + [0] * len(X_neg))

    clf = LogisticRegression(max_iter=1000, C=1.0, solver="lbfgs")
    clf.fit(X, y)

    coef = np.clip(clf.coef_[0], 0, None)
    if coef.sum() == 0:
        coef = np.ones(len(coef))
    weights = coef / coef.sum()

    result = {name: round(float(w), 4) for name, w in zip(feature_names, weights)}
    logger.info(f"{hazard} calibrated weights: {result}")
    return result


async def calibrate_all(events: List[Dict]) -> Dict[str, Dict[str, float]]:
    """
    events: list of dicts with keys: date (date), district (str), hazard_type (str)
    Returns calibrated weights dict, or defaults for any hazard with insufficient data.
    """
    from app.core.weights import DEFAULT_WEIGHTS

    flood_pos, landslide_pos, food_pos = [], [], []
    flood_neg, landslide_neg, food_neg = [], [], []

    # ── Positive samples ──────────────────────────────────────────────────────
    logger.info(f"Fetching features for {len(events)} historical events…")
    tasks = [_fetch_stats(e["district"], e["date"]) for e in events]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    for event, stats in zip(events, results):
        if isinstance(stats, Exception) or stats is None:
            logger.warning(f"Skipping {event['district']} {event['date']}: {stats}")
            continue
        h = event["hazard_type"]
        if h == "flood":
            flood_pos.append(_flood_features(stats))
        elif h == "landslide":
            landslide_pos.append(_landslide_features(stats))
        elif h == "food_stress":
            food_pos.append(_food_stress_features(stats))

    # ── Negative samples ──────────────────────────────────────────────────────
    logger.info("Fetching negative (non-event) samples…")
    neg_flood_tasks = [
        _fetch_stats(d, dt)
        for d in _FLOOD_DISTRICTS
        for dt in _NEGATIVE_DATES_FLOOD
    ]
    neg_food_tasks = [
        _fetch_stats(d, dt)
        for d in _FOOD_DISTRICTS
        for dt in _NEGATIVE_DATES_FOOD_STRESS
    ]
    neg_results = await asyncio.gather(*(neg_flood_tasks + neg_food_tasks), return_exceptions=True)

    split = len(neg_flood_tasks)
    for stats in neg_results[:split]:
        if isinstance(stats, Exception) or stats is None:
            continue
        flood_neg.append(_flood_features(stats))
        landslide_neg.append(_landslide_features(stats))

    for stats in neg_results[split:]:
        if isinstance(stats, Exception) or stats is None:
            continue
        food_neg.append(_food_stress_features(stats))

    logger.info(
        f"Samples — flood: {len(flood_pos)}+/{len(flood_neg)}-  "
        f"landslide: {len(landslide_pos)}+/{len(landslide_neg)}-  "
        f"food: {len(food_pos)}+/{len(food_neg)}-"
    )

    # ── Calibrate ─────────────────────────────────────────────────────────────
    flood_w = _fit_weights(
        flood_pos, flood_neg,
        ["rain_3d", "rain_7d", "anomaly", "floodplain"],
        "flood",
    )
    landslide_w = _fit_weights(
        landslide_pos, landslide_neg,
        ["rain_3d", "soil_moisture", "rain_7d", "slope", "baseline"],
        "landslide",
    )
    food_w = _fit_weights(
        food_pos, food_neg,
        ["rain_deficit", "heat_days", "seasonality"],
        "food_stress",
    )

    return {
        "flood":      flood_w      or DEFAULT_WEIGHTS["flood"],
        "landslide":  landslide_w  or DEFAULT_WEIGHTS["landslide"],
        "food_stress": food_w      or DEFAULT_WEIGHTS["food_stress"],
    }
