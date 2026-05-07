"""
NASA POWER API integration.
Provides:
  - Daily soil moisture (GWETROOT) for recent periods
  - 30-year monthly precipitation climatology for anomaly baseline
Free, no API key required. Coverage: 1981-present.
"""

import logging
from datetime import date
from typing import Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)

_BASE = "https://power.larc.nasa.gov/api"
_TIMEOUT = 30.0


async def fetch_soil_moisture(
    lat: float,
    lon: float,
    start_date: date,
    end_date: date,
) -> List[Dict]:
    """
    Fetch daily root-zone soil wetness (GWETROOT, 0-1 fraction of field capacity).
    Returns list of {date: str, soil_moisture: float|None}.
    """
    params = {
        "parameters": "GWETROOT",
        "community": "AG",
        "longitude": lon,
        "latitude": lat,
        "start": start_date.strftime("%Y%m%d"),
        "end": end_date.strftime("%Y%m%d"),
        "format": "JSON",
    }
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.get(f"{_BASE}/temporal/daily/point", params=params)
            resp.raise_for_status()
            resp.raise_for_status()
            data = resp.json()
    except Exception as e:
        logger.error(f"NASA POWER soil moisture fetch failed ({lat},{lon}): {e}")
        return []

    daily = data.get("properties", {}).get("parameter", {}).get("GWETROOT", {})
    results = []
    for date_str, value in daily.items():
        # NASA POWER uses -999 as fill value
        results.append({
            "date": f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}",
            "soil_moisture": float(value) if value not in (-999, -999.0) else None,
        })
    return sorted(results, key=lambda x: x["date"])


def fetch_climatological_baseline(lat: float, lon: float) -> Optional[List[float]]:
    """
    Fetch 30-year monthly precipitation climatology (mm/day averages, Jan-Dec).
    Returns list of 12 floats or None on failure.
    Uses synchronous httpx for use during startup seeding.
    """
    params = {
        "parameters": "PRECTOTCORR",
        "community": "AG",
        "longitude": lon,
        "latitude": lat,
        "format": "JSON",
    }
    try:
        with httpx.Client(timeout=_TIMEOUT) as client:
            resp = client.get(f"{_BASE}/temporal/climatology/point", params=params)
            resp.raise_for_status()
            data = resp.json()
    except Exception as e:
        logger.error(f"NASA POWER climatology fetch failed ({lat},{lon}): {e}")
        return None

    monthly = data.get("properties", {}).get("parameter", {}).get("PRECTOTCORR", {})
    # Keys are "JAN", "FEB", ..., "DEC", "ANN"
    month_keys = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN",
                  "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
    try:
        return [float(monthly[k]) for k in month_keys]
    except (KeyError, TypeError, ValueError) as e:
        logger.error(f"NASA POWER climatology parse failed: {e} — raw: {monthly}")
        return None
