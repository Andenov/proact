"""
PROACT Risk Scoring Engine
Rule-based, explainable scoring. All factor inputs are pre-normalized to [0, 1].
Outputs: score (0–100), level (Low/Medium/High), top_drivers, recommendations.
"""

from typing import Any, Dict, List, Tuple

from app.core.weights import get_flood_weights, get_landslide_weights, get_food_stress_weights


# ---------------------------------------------------------------------------
# Thresholds
# ---------------------------------------------------------------------------
FLOOD_THRESHOLDS = {"Low": 40, "Medium": 70}       # <40 Low, 40-69 Medium, >=70 High
LANDSLIDE_THRESHOLDS = {"Low": 35, "Medium": 65}   # <35 Low, 35-64 Medium, >=65 High
FOOD_STRESS_THRESHOLDS = {"Low": 30, "Medium": 60} # <30 Low, 30-59 Medium, >=60 High


# ---------------------------------------------------------------------------
# Plain-language level descriptions (what the level means in practice)
# ---------------------------------------------------------------------------
_LEVEL_DESCRIPTIONS: Dict[str, Dict[str, str]] = {
    "flood": {
        "Low":    "No significant flooding expected. {driver} is within normal range.",
        "Medium": "Localized flooding of low-lying areas possible in the next 7-14 days, driven primarily by {driver}.",
        "High":   "Significant flooding likely within 3-7 days. {driver} is at a critical level - activate emergency response now.",
    },
    "landslide": {
        "Low":    "Slopes stable. {driver} within safe limits - standard hillside monitoring is sufficient.",
        "Medium": "Elevated slope instability due to {driver}. Communities on steep terrain should stay alert and prepare to evacuate if conditions worsen.",
        "High":   "High probability of slope failure within 3-7 days. {driver} at critical levels - evacuate high-risk zones immediately.",
    },
    "food_stress": {
        "Low":    "Food security within normal range. {driver} is adequate for the current season.",
        "Medium": "Rainfall below seasonal average. {driver} suggests crop stress likely within 2-4 weeks - early coping measures advised.",
        "High":   "Severe food stress risk. {driver} at a critical deficit - food insecurity likely within 4-8 weeks without intervention.",
    },
}


def _build_description(hazard: str, level: str, top_driver_name: str) -> str:
    template = _LEVEL_DESCRIPTIONS.get(hazard, {}).get(level, "")
    return template.format(driver=top_driver_name)


# ---------------------------------------------------------------------------
# Recommendation templates
# ---------------------------------------------------------------------------
RECOMMENDATIONS: Dict[str, Dict[str, List[str]]] = {
    "flood": {
        "Low": [
            "Monitor rainfall forecasts closely.",
            "Ensure drainage channels are clear.",
        ],
        "Medium": [
            "Pre-position emergency supplies in at-risk sub-counties.",
            "Alert local leaders and community disaster officers.",
            "Advise farmers to protect stored inputs.",
        ],
        "High": [
            "Activate district emergency response plan.",
            "Pre-position food and emergency supplies immediately.",
            "Advise farmers to move livestock and protect stored grain.",
            "Inspect and avoid vulnerable routes and low-lying areas.",
            "Alert local leaders and response teams.",
        ],
    },
    "landslide": {
        "Low": [
            "Monitor cumulative rainfall in hillside areas.",
            "Remind communities of landslide-prone slopes.",
        ],
        "Medium": [
            "Alert hillside communities to increased risk.",
            "Prepare local response teams.",
            "Advise movement away from known danger zones.",
        ],
        "High": [
            "Immediately alert hillside communities.",
            "Advise evacuation from high-risk slopes where needed.",
            "Activate landslide response protocols.",
            "Protect harvests and assets in affected zones.",
            "Prepare local response teams for deployment.",
        ],
    },
    "food_stress": {
        "Low": [
            "Monitor rainfall and crop conditions weekly.",
            "Coordinate extension messaging on water conservation.",
        ],
        "Medium": [
            "Strengthen local food security monitoring.",
            "Prepare contingency food support plans.",
            "Advise farmers on drought-coping practices.",
        ],
        "High": [
            "Activate food security response mechanisms.",
            "Coordinate emergency food assistance with partners.",
            "Advise farmers on drought resilience and crop adjustment.",
            "Engage extension officers for immediate field support.",
            "Prepare for market disruption and price spike monitoring.",
        ],
    },
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _score_to_level(score: float, thresholds: Dict[str, int]) -> str:
    if score < thresholds["Low"]:
        return "Low"
    if score < thresholds["Medium"]:
        return "Medium"
    return "High"


def _normalize_rainfall(mm: float, max_mm: float = 150.0) -> float:
    """Clamp rainfall to [0, 1] using a reasonable daily max."""
    return min(mm / max_mm, 1.0) if mm and mm > 0 else 0.0


def _compute_weighted_score(factors: List[Tuple[str, float, float]]) -> Tuple[float, List[Dict]]:
    """
    factors: list of (name, normalized_value [0-1], weight)
    Returns (score_0_to_100, top_drivers)
    """
    raw = sum(v * w for _, v, w in factors)
    score = min(round(raw * 100, 1), 100.0)

    drivers = [
        {"factor": name, "contribution": round(v * w * 100, 1), "value": round(v, 3)}
        for name, v, w in factors
    ]
    drivers.sort(key=lambda d: d["contribution"], reverse=True)
    return score, drivers[:3]  # return top 3 drivers


# ---------------------------------------------------------------------------
# Flood Risk
# ---------------------------------------------------------------------------

def compute_flood_score(
    rain_3d: float,
    rain_7d: float,
    anomaly_score: float,
    floodplain_score: float,
) -> Dict[str, Any]:
    w = get_flood_weights()
    factors = [
        ("3-day rainfall", _normalize_rainfall(rain_3d, 120), w["rain_3d"]),
        ("7-day rainfall", _normalize_rainfall(rain_7d, 250), w["rain_7d"]),
        ("Rainfall anomaly", max(min((anomaly_score + 1) / 2, 1.0), 0.0), w["anomaly"]),
        ("Floodplain exposure", max(min(floodplain_score, 1.0), 0.0), w["floodplain"]),
    ]
    score, drivers = _compute_weighted_score(factors)
    level = _score_to_level(score, FLOOD_THRESHOLDS)
    return {
        "score": score,
        "level": level,
        "description": _build_description("flood", level, drivers[0]["factor"] if drivers else "rainfall"),
        "drivers": drivers,
        "recommendations": RECOMMENDATIONS["flood"][level],
    }


# ---------------------------------------------------------------------------
# Landslide Risk
# ---------------------------------------------------------------------------

def compute_landslide_score(
    rain_3d: float,
    rain_7d: float,
    slope_index: float,
    landslide_baseline_score: float,
    soil_moisture: float = 0.5,
) -> Dict[str, Any]:
    """
    soil_moisture: GWETROOT root-zone wetness fraction [0-1] from NASA POWER.
    Saturated soil (high soil_moisture) amplifies landslide risk when combined
    with heavy rainfall on steep slopes.
    """
    w = get_landslide_weights()
    factors = [
        ("3-day rainfall", _normalize_rainfall(rain_3d, 120), w["rain_3d"]),
        ("Soil moisture", max(min(soil_moisture, 1.0), 0.0), w["soil_moisture"]),
        ("7-day rainfall", _normalize_rainfall(rain_7d, 250), w["rain_7d"]),
        ("Terrain slope", max(min(slope_index, 1.0), 0.0), w["slope"]),
        ("Landslide baseline", max(min(landslide_baseline_score, 1.0), 0.0), w["baseline"]),
    ]
    score, drivers = _compute_weighted_score(factors)
    level = _score_to_level(score, LANDSLIDE_THRESHOLDS)
    return {
        "score": score,
        "level": level,
        "description": _build_description("landslide", level, drivers[0]["factor"] if drivers else "terrain conditions"),
        "drivers": drivers,
        "recommendations": RECOMMENDATIONS["landslide"][level],
    }


# ---------------------------------------------------------------------------
# Food Stress Risk
# ---------------------------------------------------------------------------
# Seasonality multipliers for Uganda (approximate planting/harvesting seasons)
# 1 = peak stress season, 0.6 = off-season
UGANDA_SEASONALITY = {
    1: 0.8, 2: 0.9, 3: 1.0, 4: 0.9,   # Mar-Apr: Long rains season
    5: 0.7, 6: 0.6, 7: 0.7, 8: 0.7,   # Dry spell / harvest
    9: 0.8, 10: 1.0, 11: 0.9, 12: 0.8, # Oct-Nov: Short rains season
}


def compute_food_stress_score(
    rain_deficit_30d: float,
    heat_stress_days: int,
    current_month: int,
) -> Dict[str, Any]:
    """
    rain_deficit_30d: mm below historical average (positive = deficit)
    heat_stress_days: number of days tmax > 35°C in past 30 days
    current_month: 1-12
    """
    deficit_norm = min(rain_deficit_30d / 100.0, 1.0) if rain_deficit_30d > 0 else 0.0
    heat_norm = min(heat_stress_days / 15.0, 1.0)
    seasonality = UGANDA_SEASONALITY.get(current_month, 0.8)

    w = get_food_stress_weights()
    factors = [
        ("Rainfall deficit (30d)", deficit_norm, w["rain_deficit"]),
        ("Heat stress days", heat_norm, w["heat_days"]),
        ("Seasonal vulnerability", seasonality, w["seasonality"]),
    ]
    score, drivers = _compute_weighted_score(factors)
    # Apply seasonality as a multiplier (amplify in peak season)
    score = min(round(score * seasonality, 1), 100.0)
    level = _score_to_level(score, FOOD_STRESS_THRESHOLDS)
    return {
        "score": score,
        "level": level,
        "description": _build_description("food_stress", level, drivers[0]["factor"] if drivers else "seasonal conditions"),
        "drivers": drivers,
        "recommendations": RECOMMENDATIONS["food_stress"][level],
    }
