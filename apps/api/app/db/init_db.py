"""
Creates all tables and loads seed data on first run.
"""

import json
import logging
import os
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.db.base import Base
from app.db.session import engine

logger = logging.getLogger(__name__)

SEED_DIR = Path("/data/seed")


def create_tables():
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
        conn.commit()
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created")


def seed_districts(db: Session):
    from app.models.district import District
    from app.models.hazard import HazardStaticFeature

    if db.query(District).count() > 0:
        return  # Already seeded

    seed_file = SEED_DIR / "districts.json"
    if not seed_file.exists():
        logger.warning(f"Seed file not found: {seed_file}")
        return

    with open(seed_file) as f:
        districts_data = json.load(f)

    for d in districts_data:
        district = District(
            name=d["name"],
            region=d["region"],
            country=d.get("country", "Uganda"),
            centroid_lat=d["centroid_lat"],
            centroid_lon=d["centroid_lon"],
            slope_index=d.get("slope_index", 0.3),
            flood_exposure_index=d.get("flood_exposure_index", 0.3),
        )
        db.add(district)
        db.flush()

        hazard = HazardStaticFeature(
            district_id=district.id,
            slope_index=d.get("slope_index", 0.3),
            elevation_mean=d.get("elevation_mean", 1200),
            river_proximity_score=d.get("river_proximity_score", 0.3),
            floodplain_score=d.get("floodplain_score", 0.3),
            landslide_baseline_score=d.get("landslide_baseline_score", 0.2),
        )
        db.add(hazard)

    db.commit()
    logger.info(f"Seeded {len(districts_data)} districts")


def seed_farmers(db: Session):
    from app.models.district import District
    from app.models.farmer import Farmer

    if db.query(Farmer).count() > 0:
        return

    seed_file = SEED_DIR / "farmers.json"
    if not seed_file.exists():
        return

    with open(seed_file) as f:
        farmers_data = json.load(f)

    districts = {d.name: d.id for d in db.query(District).all()}

    for f in farmers_data:
        farmer = Farmer(
            full_name=f.get("full_name"),
            phone_number=f["phone_number"],
            district_id=districts.get(f.get("district_name")),
            preferred_language=f.get("preferred_language", "en"),
            consent_status=f.get("consent_status", True),
        )
        db.add(farmer)

    db.commit()
    logger.info(f"Seeded {len(farmers_data)} farmers")


def seed_admin_user(db: Session):
    from app.models.user import User

    if db.query(User).count() > 0:
        return

    admin = User(
        full_name="PROACT Admin",
        email="admin@proact.org",
        password_hash=hash_password("proact2024"),
        role="admin",
        organization="PROACT",
    )
    db.add(admin)
    db.commit()
    logger.info("Admin user seeded: admin@proact.org / proact2024")


def seed_climate_baselines(db: Session):
    """Fetch 30-year monthly precipitation climatology from NASA POWER for each district."""
    from app.models.district import District
    from app.models.hazard import HazardStaticFeature
    from app.services.nasa_power_service import fetch_climatological_baseline

    hazards = db.query(HazardStaticFeature).all()
    districts = {d.id: d for d in db.query(District).all()}

    for hazard in hazards:
        if hazard.rainfall_monthly_avg_json:
            continue  # Already seeded
        district = districts.get(hazard.district_id)
        if not district or not district.centroid_lat:
            continue
        baseline = fetch_climatological_baseline(district.centroid_lat, district.centroid_lon)
        if baseline:
            hazard.rainfall_monthly_avg_json = json.dumps(baseline)
            logger.info(f"Seeded climatological baseline for {district.name}")
        else:
            logger.warning(f"Could not fetch baseline for {district.name}, will use fallback")

    db.commit()


def init_db(db: Session):
    create_tables()
    seed_districts(db)
    seed_farmers(db)
    seed_admin_user(db)
    seed_climate_baselines(db)
