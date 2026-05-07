"""
Risk engine weight loader.

Loads calibrated weights from weights.json if available.
Falls back to hand-tuned defaults if the file is missing or invalid.
After running scripts/calibrate_weights.py, restart the API to apply new weights.
"""

import json
import logging
from pathlib import Path
from typing import Dict

logger = logging.getLogger(__name__)

_WEIGHTS_FILE = Path(__file__).parent / "weights.json"

DEFAULT_WEIGHTS: Dict[str, Dict[str, float]] = {
    "flood": {
        "rain_3d":    0.35,
        "rain_7d":    0.25,
        "anomaly":    0.25,
        "floodplain": 0.15,
    },
    "landslide": {
        "rain_3d":       0.30,
        "soil_moisture": 0.25,
        "rain_7d":       0.20,
        "slope":         0.15,
        "baseline":      0.10,
    },
    "food_stress": {
        "rain_deficit": 0.50,
        "heat_days":    0.30,
        "seasonality":  0.20,
    },
}


def _load() -> Dict[str, Dict[str, float]]:
    if _WEIGHTS_FILE.exists():
        try:
            with open(_WEIGHTS_FILE) as f:
                data = json.load(f)
            logger.info(f"Loaded calibrated weights from {_WEIGHTS_FILE}")
            return data
        except Exception as e:
            logger.warning(f"Failed to load weights.json ({e}), using defaults")
    return DEFAULT_WEIGHTS


_weights = _load()


def get_flood_weights() -> Dict[str, float]:
    return _weights.get("flood", DEFAULT_WEIGHTS["flood"])


def get_landslide_weights() -> Dict[str, float]:
    return _weights.get("landslide", DEFAULT_WEIGHTS["landslide"])


def get_food_stress_weights() -> Dict[str, float]:
    return _weights.get("food_stress", DEFAULT_WEIGHTS["food_stress"])


def get_all_weights() -> Dict[str, Dict[str, float]]:
    return _weights


def is_calibrated() -> bool:
    return _WEIGHTS_FILE.exists()
