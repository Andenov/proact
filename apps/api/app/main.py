import logging
import threading
from contextlib import asynccontextmanager
from datetime import date

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.db.session import SessionLocal
from app.db.init_db import init_db
from app.jobs.scheduler import start_scheduler, stop_scheduler
from app.routes import alerts, auth, districts, farmers, health, ingest, risk, sms, storage

logging.basicConfig(level=getattr(logging, settings.LOG_LEVEL, logging.INFO))
logger = logging.getLogger(__name__)


def _startup_catchup():
    """Run the daily pipeline and backfill history if data is stale or missing."""
    from app.models.weather import WeatherObservation
    from app.models.risk_score import DistrictRiskScore
    from app.jobs.tasks import run_daily_pipeline, backfill_risk_scores

    db = SessionLocal()
    try:
        latest_obs = (
            db.query(WeatherObservation)
            .order_by(WeatherObservation.date.desc())
            .first()
        )
        risk_count = db.query(DistrictRiskScore).count()

        if latest_obs is None or latest_obs.date < date.today():
            logger.info(
                "Data stale (latest obs: %s) — running catch-up pipeline in background",
                latest_obs.date if latest_obs else "none",
            )
            threading.Thread(target=run_daily_pipeline, daemon=True).start()
        else:
            logger.info("Data current (%s) — no catch-up needed", latest_obs.date)

        # Backfill historical scores for charts if fewer than 25 rows exist
        if risk_count < 25:
            logger.info("Risk score history sparse (%d rows) — backfilling 30 days", risk_count)
            threading.Thread(
                target=lambda: _run_backfill(), daemon=True
            ).start()
    except Exception as exc:
        logger.warning("Catch-up check failed: %s", exc)
    finally:
        db.close()


def _run_backfill():
    from app.jobs.tasks import backfill_risk_scores
    db = SessionLocal()
    try:
        backfill_risk_scores(db, days_back=30)
        logger.info("Historical risk score backfill complete")
    except Exception as exc:
        logger.error("Backfill failed: %s", exc)
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting PROACT API...")
    db = SessionLocal()
    try:
        init_db(db)
    finally:
        db.close()
    start_scheduler()
    _startup_catchup()
    yield
    stop_scheduler()
    logger.info("PROACT API shutting down")


app = FastAPI(
    title="PROACT API",
    description="Anticipatory action platform for climate risk and farmer alerting",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(districts.router)
app.include_router(risk.router)
app.include_router(alerts.router)
app.include_router(farmers.router)
app.include_router(sms.router)
app.include_router(ingest.router)
app.include_router(storage.router)
