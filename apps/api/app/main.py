import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.db.session import SessionLocal
from app.db.init_db import init_db
from app.jobs.scheduler import start_scheduler, stop_scheduler
from app.routes import alerts, auth, districts, farmers, health, ingest, risk, sms

logging.basicConfig(level=getattr(logging, settings.LOG_LEVEL, logging.INFO))
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting PROACT API...")
    db = SessionLocal()
    try:
        init_db(db)
    finally:
        db.close()
    start_scheduler()
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
