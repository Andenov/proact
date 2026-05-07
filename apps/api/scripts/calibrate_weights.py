#!/usr/bin/env python3
"""
Calibrate PROACT risk engine weights from historical disaster events.

Run from the apps/api/ directory:
    python scripts/calibrate_weights.py

Reads:  data/events/historical_events.csv
Writes: app/core/weights.json

After running, restart the API for new weights to take effect.
"""

import asyncio
import csv
import json
import logging
import sys
from datetime import date
from pathlib import Path

# Allow importing app modules when run from apps/api/
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.calibration import calibrate_all

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
logger = logging.getLogger(__name__)

EVENTS_FILE  = Path(__file__).parent.parent / "data" / "events" / "historical_events.csv"
WEIGHTS_FILE = Path(__file__).parent.parent / "app" / "core" / "weights.json"


def load_events() -> list:
    events = []
    with open(EVENTS_FILE, newline="") as f:
        for row in csv.DictReader(f):
            try:
                events.append({
                    "date":        date.fromisoformat(row["date"]),
                    "district":    row["district"].strip(),
                    "hazard_type": row["hazard_type"].strip(),
                    "severity":    row["severity"].strip(),
                })
            except (KeyError, ValueError) as e:
                logger.warning(f"Skipping bad row {row}: {e}")
    return events


async def main():
    logger.info(f"Loading events from {EVENTS_FILE}")
    events = load_events()
    logger.info(f"Loaded {len(events)} events")

    weights = await calibrate_all(events)

    with open(WEIGHTS_FILE, "w") as f:
        json.dump(weights, f, indent=2)

    logger.info(f"\nCalibrated weights saved to {WEIGHTS_FILE}")
    logger.info("Restart the API to apply new weights.\n")

    for hazard, w in weights.items():
        logger.info(f"  {hazard}: {w}")


if __name__ == "__main__":
    asyncio.run(main())
