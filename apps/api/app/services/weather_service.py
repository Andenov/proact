"""
Open-Meteo weather data fetcher.
Fetches historical + forecast precipitation and temperature for a lat/lon point.
"""

import logging
from datetime import date, timedelta
from typing import Dict, List, Optional

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


async def fetch_weather_for_district(
    lat: float,
    lon: float,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
) -> List[Dict]:
    """
    Fetch daily weather observations from Open-Meteo archive + forecast APIs.
    Returns list of dicts: {date, rainfall_mm, tmin_c, tmax_c}
    """
    if end_date is None:
        end_date = date.today()
    if start_date is None:
        start_date = end_date - timedelta(days=37)  # 30d historical + 7d forecast

    today = date.today()
    results: List[Dict] = []

    # Split: historical (up to yesterday) and forecast (today+)
    hist_end = min(end_date, today - timedelta(days=1))
    fcast_start = max(start_date, today)

    async with httpx.AsyncClient(timeout=30.0) as client:
        # --- Historical ---
        if start_date <= hist_end:
            params = {
                "latitude": lat,
                "longitude": lon,
                "start_date": start_date.isoformat(),
                "end_date": hist_end.isoformat(),
                "daily": "precipitation_sum,temperature_2m_max,temperature_2m_min",
                "timezone": "Africa/Kampala",
            }
            try:
                resp = await client.get(
                    f"{settings.OPEN_METEO_ARCHIVE_URL}/archive", params=params
                )
                resp.raise_for_status()
                data = resp.json()
                results.extend(_parse_daily(data))
            except Exception as e:
                logger.error(f"Open-Meteo archive error for ({lat},{lon}): {e}")

        # --- Forecast ---
        if fcast_start <= end_date:
            params = {
                "latitude": lat,
                "longitude": lon,
                "daily": "precipitation_sum,temperature_2m_max,temperature_2m_min",
                "timezone": "Africa/Kampala",
                "forecast_days": min((end_date - fcast_start).days + 1, 16),
            }
            try:
                resp = await client.get(
                    f"{settings.OPEN_METEO_BASE_URL}/forecast", params=params
                )
                resp.raise_for_status()
                data = resp.json()
                results.extend(_parse_daily(data))
            except Exception as e:
                logger.error(f"Open-Meteo forecast error for ({lat},{lon}): {e}")

    return results


def _parse_daily(data: Dict) -> List[Dict]:
    daily = data.get("daily", {})
    dates = daily.get("time", [])
    precip = daily.get("precipitation_sum", [])
    tmax = daily.get("temperature_2m_max", [])
    tmin = daily.get("temperature_2m_min", [])

    rows = []
    for i, d in enumerate(dates):
        rows.append({
            "date": d,
            "rainfall_mm": precip[i] if i < len(precip) else None,
            "tmax_c": tmax[i] if i < len(tmax) else None,
            "tmin_c": tmin[i] if i < len(tmin) else None,
        })
    return rows


def compute_rolling_stats(
    observations: List[Dict],
    monthly_baseline_mm_per_day: Optional[List[float]] = None,
) -> Dict:
    """
    Given a list of {date, rainfall_mm, tmax_c, soil_moisture, ...} sorted ascending,
    compute rolling stats needed by the risk engine.

    monthly_baseline_mm_per_day: 12-element list of 30-year avg daily rainfall (mm/day)
    for Jan-Dec from NASA POWER climatology. Used for anomaly and deficit calculation.
    Falls back to observed mean if not provided.
    """
    import pandas as pd

    if not observations:
        return {}

    df = pd.DataFrame(observations)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)
    df["rainfall_mm"] = pd.to_numeric(df["rainfall_mm"], errors="coerce").fillna(0)
    df["tmax_c"] = pd.to_numeric(df["tmax_c"], errors="coerce")

    latest = df.iloc[-1]
    current_month = latest["date"].month  # 1-12

    rain_3d = df["rainfall_mm"].tail(3).sum()
    rain_7d = df["rainfall_mm"].tail(7).sum()
    rain_30d = df["rainfall_mm"].tail(30).sum()

    # Use NASA POWER 30-year climatology baseline if available
    if monthly_baseline_mm_per_day and len(monthly_baseline_mm_per_day) == 12:
        # Average daily baseline for current month (mm/day) → 30-day expected total
        clim_daily = monthly_baseline_mm_per_day[current_month - 1]
        hist_avg_30d = clim_daily * 30
        # Anomaly: how much above/below the climatological daily mean is our 7-day avg
        clim_7d_avg = clim_daily * 7
        observed_7d_avg = float(rain_7d)
        std_estimate = max(clim_daily * 10, 1.0)  # rough seasonal std estimate
        anomaly = (observed_7d_avg - clim_7d_avg) / std_estimate
    else:
        # Fallback: use observed mean (weak but better than nothing)
        hist_avg_30d = float(df["rainfall_mm"].mean()) * 30
        mean_30d = float(df["rainfall_mm"].tail(30).mean())
        std_30d = float(df["rainfall_mm"].tail(30).std()) or 1.0
        anomaly = (float(rain_7d) / 7 - mean_30d) / std_30d

    anomaly = max(min(anomaly, 1.0), -1.0)
    rain_deficit_30d = max(hist_avg_30d - float(rain_30d), 0)

    heat_stress_days = int((df["tmax_c"].tail(30) > 35).sum()) if "tmax_c" in df.columns else 0

    # Soil moisture: use the most recent non-null reading (NASA POWER has no forecast)
    soil_moisture = None
    if "soil_moisture" in df.columns:
        non_null_sm = df["soil_moisture"].dropna()
        if not non_null_sm.empty:
            soil_moisture = float(non_null_sm.iloc[-1])

    return {
        "rain_3d": round(float(rain_3d), 1),
        "rain_7d": round(float(rain_7d), 1),
        "rain_30d": round(float(rain_30d), 1),
        "rain_deficit_30d": round(rain_deficit_30d, 1),
        "anomaly_score": round(anomaly, 3),
        "heat_stress_days": heat_stress_days,
        "soil_moisture": soil_moisture,
        "latest_date": str(latest["date"].date()),
    }
