import asyncio
import logging
from datetime import date, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.jobs.tasks import backfill_risk_scores, compute_all_risks, ingest_weather_all

router = APIRouter(prefix="/ingest", tags=["ingest"])
logger = logging.getLogger(__name__)


@router.post("/weather")
async def trigger_ingest_weather(
    days_back: int = 37,
    db: Session = Depends(get_db),
):
    """Fetch and store weather observations for all districts."""
    result = await ingest_weather_all(db, days_back=days_back)
    return result


@router.post("/compute-risk")
def trigger_compute_risk(db: Session = Depends(get_db)):
    """Recompute risk scores for all districts using latest weather data."""
    result = compute_all_risks(db)
    return result


@router.post("/backfill")
def trigger_backfill(days_back: int = 30, db: Session = Depends(get_db)):
    """Backfill historical risk scores for charting."""
    result = backfill_risk_scores(db, days_back=days_back)
    return result
