"""
Smart Grain Storage — Aflatoxin Risk Scoring Engine

Inputs: silo sensor readings + ambient PROACT weather data per district
Output: score (0-100), level (Low/Medium/High), top drivers, predicted_days_safe, recommendations

Science basis: aflatoxin growth requires moisture > 13.5% AND temp > 28 C simultaneously.
Both factors together are multiplicative; alone they are insufficient.
"""

from typing import Any, Dict, List


STORAGE_THRESHOLDS = {"Low": 30, "Medium": 60}  # <30 Low, 30-59 Medium, >=60 High

WEIGHTS = {
    "moisture":  0.40,
    "temp":      0.25,
    "humidity":  0.15,
    "co2":       0.10,
    "ambient":   0.10,
}

LEVEL_DESCRIPTIONS = {
    "Low":    "Storage conditions safe. {driver} within acceptable limits — grain secure for extended storage.",
    "Medium": "Elevated aflatoxin risk due to {driver}. Conditions may deteriorate without action in the next 2-4 weeks.",
    "High":   "Critical aflatoxin risk. {driver} at dangerous level — grain likely unsafe within 7 days without immediate intervention.",
}

RECOMMENDATIONS: Dict[str, List[str]] = {
    "Low": [
        "Conditions good. Continue monitoring weekly.",
        "Maintain seal integrity and keep storage away from direct sunlight.",
    ],
    "Medium": [
        "Moisture or temperature approaching risk threshold.",
        "Check seal for breaches and ensure good ventilation around the silo.",
        "Consider selling within 2-4 weeks if conditions worsen.",
        "Increase reading frequency to daily.",
    ],
    "High": [
        "URGENT: Aflatoxin conditions present. Act immediately.",
        "Dry grain to below 13% moisture before re-sealing.",
        "Sell or use grain within the next 7 days.",
        "Separate any visibly moldy grain to prevent spread.",
        "Contact extension officer for immediate assessment.",
    ],
}


# ---------------------------------------------------------------------------
# Normalization helpers
# ---------------------------------------------------------------------------

def _norm_moisture(v: float) -> float:
    """Critical threshold 13.5%. Above 16% = fully unsafe."""
    if v <= 13.0:
        return 0.0
    if v >= 16.0:
        return 1.0
    return (v - 13.0) / 3.0


def _norm_temp(v: float) -> float:
    """Safe below 25 C. Critical above 35 C."""
    if v <= 25.0:
        return 0.0
    if v >= 35.0:
        return 1.0
    return (v - 25.0) / 10.0


def _norm_humidity(v: float) -> float:
    """Internal relative humidity. Safe below 60%."""
    if v <= 60.0:
        return 0.0
    if v >= 85.0:
        return 1.0
    return (v - 60.0) / 25.0


def _norm_co2(v: float) -> float:
    """CO2 rise inside sealed container signals insect activity.
    Normal: 400-800 ppm. Insect infestation: >2000 ppm."""
    if v <= 800.0:
        return 0.0
    if v >= 3000.0:
        return 1.0
    return (v - 800.0) / 2200.0


def _norm_ambient(ambient_temp_c: float, rainfall_7d_mm: float) -> float:
    """High ambient temp and recent rainfall both raise internal silo pressure."""
    t = max(0.0, min((ambient_temp_c - 25.0) / 10.0, 1.0))
    r = min(rainfall_7d_mm / 100.0, 1.0)
    return t * 0.6 + r * 0.4


# ---------------------------------------------------------------------------
# Core
# ---------------------------------------------------------------------------

def _score_to_level(score: float) -> str:
    if score < STORAGE_THRESHOLDS["Low"]:
        return "Low"
    if score < STORAGE_THRESHOLDS["Medium"]:
        return "Medium"
    return "High"


def predict_days_safe(score: float, moisture_pct: float, temp_c: float) -> int:
    """Estimate days before conditions become unsafe for grain storage."""
    if score >= STORAGE_THRESHOLDS["Medium"]:
        # High combined risk — days remaining depend on how far above threshold
        if moisture_pct > 15.0 and temp_c > 30.0:
            return max(0, round((100 - score) / 8))
        return max(5, round((100 - score) / 5))
    # Low risk — estimate days until Medium threshold based on rate factors
    gap = STORAGE_THRESHOLDS["Low"] - score
    # Growth rate driven by how close conditions are to the danger thresholds
    moisture_pressure = max(0.0, moisture_pct - 13.0) * 0.8
    temp_pressure = max(0.0, temp_c - 25.0) * 0.3
    daily_rate = max(0.1, moisture_pressure + temp_pressure)
    return min(180, max(14, round(gap / daily_rate)))


def compute_aflatoxin_score(
    moisture_pct: float,
    temp_c: float,
    humidity_pct: float,
    co2_ppm: float,
    days_sealed: int,
    ambient_temp_c: float = 28.0,
    rainfall_7d_mm: float = 20.0,
) -> Dict[str, Any]:
    """
    moisture_pct   : grain moisture content (%)
    temp_c         : silo internal temperature (Celsius)
    humidity_pct   : relative humidity inside silo (%)
    co2_ppm        : CO2 concentration (ppm) — proxy for insect activity
    days_sealed    : days since silo was last sealed
    ambient_temp_c : district ambient temperature from PROACT weather
    rainfall_7d_mm : district 7-day rainfall from PROACT weather
    """
    m = _norm_moisture(moisture_pct)
    t = _norm_temp(temp_c)
    h = _norm_humidity(humidity_pct)
    c = _norm_co2(co2_ppm)
    a = _norm_ambient(ambient_temp_c, rainfall_7d_mm)

    raw = (
        m * WEIGHTS["moisture"] +
        t * WEIGHTS["temp"] +
        h * WEIGHTS["humidity"] +
        c * WEIGHTS["co2"] +
        a * WEIGHTS["ambient"]
    )

    # Grain stored longer with borderline conditions accumulates risk
    # Amplify score by up to 20% for grain sealed more than 2 weeks
    time_factor = min(max(days_sealed - 14, 0) / 76.0, 1.0)  # 0→1 over days 14-90
    time_amplifier = 1.0 + 0.20 * time_factor

    score = min(round(raw * 100 * time_amplifier, 1), 100.0)
    level = _score_to_level(score)

    drivers = sorted([
        {"factor": "Grain moisture",     "contribution": round(m * WEIGHTS["moisture"] * 100, 1), "value": round(m, 3), "raw": f"{moisture_pct:.1f}%"},
        {"factor": "Storage temperature","contribution": round(t * WEIGHTS["temp"]     * 100, 1), "value": round(t, 3), "raw": f"{temp_c:.1f} C"},
        {"factor": "Relative humidity",  "contribution": round(h * WEIGHTS["humidity"] * 100, 1), "value": round(h, 3), "raw": f"{humidity_pct:.1f}%"},
        {"factor": "CO2 level",          "contribution": round(c * WEIGHTS["co2"]      * 100, 1), "value": round(c, 3), "raw": f"{co2_ppm:.0f} ppm"},
        {"factor": "Ambient conditions", "contribution": round(a * WEIGHTS["ambient"]  * 100, 1), "value": round(a, 3), "raw": f"{ambient_temp_c:.1f} C amb"},
    ], key=lambda d: d["contribution"], reverse=True)

    top_driver_name = drivers[0]["factor"] if drivers else "storage conditions"
    description = LEVEL_DESCRIPTIONS[level].format(driver=top_driver_name)
    days_safe = predict_days_safe(score, moisture_pct, temp_c)

    return {
        "score": score,
        "level": level,
        "description": description,
        "top_drivers": drivers[:3],
        "predicted_days_safe": days_safe,
        "recommendations": RECOMMENDATIONS[level],
    }
