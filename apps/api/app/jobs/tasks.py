"""
Core pipeline tasks: ingest weather → compute risk → generate alerts.
These are called by the scheduler and by the /ingest endpoints.
"""

import json
import logging
from datetime import date, timedelta
from typing import Dict

from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.district import District
from app.models.hazard import HazardStaticFeature
from app.models.risk_score import DistrictRiskScore
from app.models.weather import WeatherObservation
from app.services.alert_service import generate_alerts_from_scores
from app.services.nasa_power_service import fetch_soil_moisture
from app.services.risk_engine import (
    compute_flood_score,
    compute_food_stress_score,
    compute_landslide_score,
)
from app.services.weather_service import (
    compute_rolling_stats,
    fetch_weather_for_district,
)

logger = logging.getLogger(__name__)


async def ingest_weather_all(db: Session, days_back: int = 37) -> Dict:
    """Fetch and upsert weather observations (Open-Meteo) and soil moisture (NASA POWER)."""
    districts = db.query(District).all()
    end_date = date.today() + timedelta(days=16)
    start_date = date.today() - timedelta(days=days_back)
    total_rows = 0

    for district in districts:
        if not district.centroid_lat or not district.centroid_lon:
            logger.warning(f"Skipping {district.name}: no centroid")
            continue

        # Fetch weather from Open-Meteo
        try:
            observations = await fetch_weather_for_district(
                lat=district.centroid_lat,
                lon=district.centroid_lon,
                start_date=start_date,
                end_date=end_date,
            )
        except Exception as e:
            logger.error(f"Weather fetch failed for {district.name}: {e}")
            observations = []

        # Fetch soil moisture from NASA POWER (historical only; no forecast available)
        sm_by_date: Dict[str, float] = {}
        try:
            sm_rows = await fetch_soil_moisture(
                lat=district.centroid_lat,
                lon=district.centroid_lon,
                start_date=start_date,
                end_date=date.today(),
            )
            sm_by_date = {r["date"]: r["soil_moisture"] for r in sm_rows if r["soil_moisture"] is not None}
        except Exception as e:
            logger.warning(f"Soil moisture fetch failed for {district.name}: {e}")

        for obs in observations:
            obs_date = obs["date"] if isinstance(obs["date"], date) else date.fromisoformat(obs["date"])
            soil_moisture = sm_by_date.get(str(obs_date))
            existing = (
                db.query(WeatherObservation)
                .filter(
                    WeatherObservation.district_id == district.id,
                    WeatherObservation.date == obs_date,
                )
                .first()
            )
            if existing:
                existing.rainfall_mm = obs.get("rainfall_mm")
                existing.tmax_c = obs.get("tmax_c")
                existing.tmin_c = obs.get("tmin_c")
                if soil_moisture is not None:
                    existing.soil_moisture = soil_moisture
            else:
                row = WeatherObservation(
                    district_id=district.id,
                    date=obs_date,
                    rainfall_mm=obs.get("rainfall_mm"),
                    tmax_c=obs.get("tmax_c"),
                    tmin_c=obs.get("tmin_c"),
                    soil_moisture=soil_moisture,
                    source="open-meteo+nasa-power",
                )
                db.add(row)
                total_rows += 1

        db.commit()
        logger.info(f"Ingested weather+soil_moisture for {district.name} ({len(sm_by_date)} SM readings)")

    return {"districts_processed": len(districts), "new_rows": total_rows}


def compute_all_risks(db: Session) -> Dict:
    """Compute and upsert risk scores for all districts using latest weather data."""
    districts = db.query(District).all()
    today = date.today()
    computed = 0

    for district in districts:
        hazard = (
            db.query(HazardStaticFeature)
            .filter(HazardStaticFeature.district_id == district.id)
            .first()
        )
        floodplain = hazard.floodplain_score if hazard else 0.3
        slope = hazard.slope_index if hazard else 0.3
        landslide_baseline = hazard.landslide_baseline_score if hazard else 0.2

        # Load monthly climatological baseline if available
        monthly_baseline = None
        if hazard and hazard.rainfall_monthly_avg_json:
            try:
                monthly_baseline = json.loads(hazard.rainfall_monthly_avg_json)
            except (json.JSONDecodeError, TypeError):
                pass

        # Load last 37 days of weather
        obs_rows = (
            db.query(WeatherObservation)
            .filter(
                WeatherObservation.district_id == district.id,
                WeatherObservation.date >= today - timedelta(days=37),
            )
            .order_by(WeatherObservation.date.asc())
            .all()
        )

        obs_dicts = [
            {
                "date": str(o.date),
                "rainfall_mm": o.rainfall_mm or 0,
                "tmax_c": o.tmax_c,
                "tmin_c": o.tmin_c,
                "soil_moisture": o.soil_moisture,
            }
            for o in obs_rows
        ]

        if not obs_dicts:
            logger.warning(f"No weather data for {district.name}, using zero defaults")
            stats = {"rain_3d": 0, "rain_7d": 0, "rain_30d": 0, "rain_deficit_30d": 0,
                     "anomaly_score": 0, "heat_stress_days": 0, "soil_moisture": None}
        else:
            stats = compute_rolling_stats(obs_dicts, monthly_baseline_mm_per_day=monthly_baseline)

        soil_moisture = stats.get("soil_moisture") or 0.5  # default to mid-range if unknown

        flood_result = compute_flood_score(
            rain_3d=stats.get("rain_3d", 0),
            rain_7d=stats.get("rain_7d", 0),
            anomaly_score=stats.get("anomaly_score", 0),
            floodplain_score=floodplain,
        )
        landslide_result = compute_landslide_score(
            rain_3d=stats.get("rain_3d", 0),
            rain_7d=stats.get("rain_7d", 0),
            slope_index=slope,
            landslide_baseline_score=landslide_baseline,
            soil_moisture=soil_moisture,
        )
        food_result = compute_food_stress_score(
            rain_deficit_30d=stats.get("rain_deficit_30d", 0),
            heat_stress_days=stats.get("heat_stress_days", 0),
            current_month=today.month,
        )

        top_drivers = {
            "flood": flood_result["drivers"],
            "landslide": landslide_result["drivers"],
            "food_stress": food_result["drivers"],
            "descriptions": {
                "flood": flood_result["description"],
                "landslide": landslide_result["description"],
                "food_stress": food_result["description"],
            },
        }
        recommendations = {
            "flood": flood_result["recommendations"],
            "landslide": landslide_result["recommendations"],
            "food_stress": food_result["recommendations"],
        }

        existing = (
            db.query(DistrictRiskScore)
            .filter(
                DistrictRiskScore.district_id == district.id,
                DistrictRiskScore.date == today,
            )
            .first()
        )
        if existing:
            existing.flood_score = float(flood_result["score"])
            existing.flood_level = flood_result["level"]
            existing.landslide_score = float(landslide_result["score"])
            existing.landslide_level = landslide_result["level"]
            existing.food_stress_score = float(food_result["score"])
            existing.food_stress_level = food_result["level"]
            existing.top_drivers_json = top_drivers
            existing.recommendations_json = recommendations
        else:
            score_row = DistrictRiskScore(
                district_id=district.id,
                date=today,
                flood_score=float(flood_result["score"]),
                flood_level=flood_result["level"],
                landslide_score=float(landslide_result["score"]),
                landslide_level=landslide_result["level"],
                food_stress_score=float(food_result["score"]),
                food_stress_level=food_result["level"],
                top_drivers_json=top_drivers,
                recommendations_json=recommendations,
            )
            db.add(score_row)

        computed += 1
        logger.info(
            f"{district.name}: flood={flood_result['level']} "
            f"landslide={landslide_result['level']} "
            f"food_stress={food_result['level']} "
            f"soil_moisture={soil_moisture:.2f}"
        )

    db.commit()
    return {"districts_computed": computed, "date": str(today)}


def backfill_risk_scores(db: Session, days_back: int = 30) -> Dict:
    """Compute risk scores for each past date using historical weather data."""
    districts = db.query(District).all()
    today = date.today()
    total = 0

    for district in districts:
        hazard = (
            db.query(HazardStaticFeature)
            .filter(HazardStaticFeature.district_id == district.id)
            .first()
        )
        floodplain = hazard.floodplain_score if hazard else 0.3
        slope = hazard.slope_index if hazard else 0.3
        landslide_baseline = hazard.landslide_baseline_score if hazard else 0.2

        monthly_baseline = None
        if hazard and hazard.rainfall_monthly_avg_json:
            try:
                monthly_baseline = json.loads(hazard.rainfall_monthly_avg_json)
            except Exception:
                pass

        # All weather rows for this district, sorted ascending
        all_obs = (
            db.query(WeatherObservation)
            .filter(WeatherObservation.district_id == district.id)
            .order_by(WeatherObservation.date.asc())
            .all()
        )
        if not all_obs:
            continue

        # Compute a score for each historical date (skip future)
        for target_date in (today - timedelta(days=i) for i in range(days_back, 0, -1)):
            # Skip if score already exists
            existing = (
                db.query(DistrictRiskScore)
                .filter(
                    DistrictRiskScore.district_id == district.id,
                    DistrictRiskScore.date == target_date,
                )
                .first()
            )
            if existing:
                continue

            # Use weather up to and including target_date
            obs_rows = [o for o in all_obs if o.date <= target_date]
            obs_rows = obs_rows[-37:]  # last 37 days relative to target
            if not obs_rows:
                continue

            obs_dicts = [
                {
                    "date": str(o.date),
                    "rainfall_mm": o.rainfall_mm or 0,
                    "tmax_c": o.tmax_c,
                    "tmin_c": o.tmin_c,
                    "soil_moisture": o.soil_moisture,
                }
                for o in obs_rows
            ]

            stats = compute_rolling_stats(obs_dicts, monthly_baseline_mm_per_day=monthly_baseline)
            soil_moisture = stats.get("soil_moisture") or 0.5

            flood_result = compute_flood_score(
                rain_3d=stats.get("rain_3d", 0),
                rain_7d=stats.get("rain_7d", 0),
                anomaly_score=stats.get("anomaly_score", 0),
                floodplain_score=floodplain,
            )
            landslide_result = compute_landslide_score(
                rain_3d=stats.get("rain_3d", 0),
                rain_7d=stats.get("rain_7d", 0),
                slope_index=slope,
                landslide_baseline_score=landslide_baseline,
                soil_moisture=soil_moisture,
            )
            food_result = compute_food_stress_score(
                rain_deficit_30d=stats.get("rain_deficit_30d", 0),
                heat_stress_days=stats.get("heat_stress_days", 0),
                current_month=target_date.month,
            )

            db.add(DistrictRiskScore(
                district_id=district.id,
                date=target_date,
                flood_score=float(flood_result["score"]),
                flood_level=flood_result["level"],
                landslide_score=float(landslide_result["score"]),
                landslide_level=landslide_result["level"],
                food_stress_score=float(food_result["score"]),
                food_stress_level=food_result["level"],
                top_drivers_json={"flood": flood_result["drivers"], "landslide": landslide_result["drivers"], "food_stress": food_result["drivers"]},
                recommendations_json={"flood": flood_result["recommendations"], "landslide": landslide_result["recommendations"], "food_stress": food_result["recommendations"]},
            ))
            total += 1

        db.commit()
        logger.info(f"Backfilled {total} risk score rows for {district.name}")

    return {"backfilled": total, "days_back": days_back}


def run_daily_pipeline():
    """Called by APScheduler. Runs the full ingest → compute → alert pipeline."""
    import asyncio
    db = SessionLocal()
    try:
        asyncio.run(ingest_weather_all(db))
        compute_all_risks(db)
        generate_alerts_from_scores(db)
        logger.info("Daily pipeline completed successfully")
    except Exception as e:
        logger.error(f"Daily pipeline failed: {e}")
    finally:
        db.close()
