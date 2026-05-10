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
    """Run the daily pipeline immediately if weather data is stale."""
    from app.models.weather import WeatherObservation
    from app.jobs.tasks import run_daily_pipeline

    db = SessionLocal()
    try:
        latest = (
            db.query(WeatherObservation)
            .order_by(WeatherObservation.date.desc())
            .first()
        )
        if latest is None or latest.date < date.today():
            logger.info(
                "Data stale (latest obs: %s) — running catch-up pipeline in background",
                latest.date if latest else "none",
            )
            threading.Thread(target=run_daily_pipeline, daemon=True).start()
        else:
            logger.info("Data current (%s) — no catch-up needed", latest.date)
    except Exception as exc:
        logger.warning("Catch-up check failed: %s", exc)
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
