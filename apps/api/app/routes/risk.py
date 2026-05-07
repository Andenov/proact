from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.models.district import District
from app.models.risk_score import DistrictRiskScore
from app.schemas.risk import RiskScoreOut
from app.services.forecast_service import compute_risk_horizons

router = APIRouter(prefix="/risk", tags=["risk"])


def _enrich(score: DistrictRiskScore, db: Session) -> RiskScoreOut:
    district = db.query(District).filter(District.id == score.district_id).first()
    out = RiskScoreOut.model_validate(score)
    out.district_name = district.name if district else None
    return out


@router.get("/latest", response_model=List[RiskScoreOut])
def latest_risk(
    type: Optional[str] = Query(None, description="flood | landslide | food_stress"),
    district_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
):
    """Return the most recent risk score per district."""
    from sqlalchemy import func

    subq = (
        db.query(
            DistrictRiskScore.district_id,
            func.max(DistrictRiskScore.date).label("max_date"),
        )
        .group_by(DistrictRiskScore.district_id)
        .subquery()
    )

    q = db.query(DistrictRiskScore).join(
        subq,
        (DistrictRiskScore.district_id == subq.c.district_id)
        & (DistrictRiskScore.date == subq.c.max_date),
    )

    if district_id:
        q = q.filter(DistrictRiskScore.district_id == district_id)

    scores = q.all()
    return [_enrich(s, db) for s in scores]


@router.get("/horizons/{district_id}", response_model=List[Dict[str, Any]])
def risk_horizons(district_id: int, db: Session = Depends(get_db)):
    """
    Return risk scores for 4 time horizons: today, 7d, 14d, 30d.
    Uses forecast data already ingested + climatological fill beyond 16 days.
    """
    district = db.query(District).filter(District.id == district_id).first()
    if not district:
        raise HTTPException(status_code=404, detail="District not found")
    return compute_risk_horizons(district_id, db)


@router.get("/history", response_model=List[RiskScoreOut])
def risk_history(
    district_id: int = Query(...),
    limit: int = Query(30, ge=1, le=90),
    db: Session = Depends(get_db),
):
    scores = (
        db.query(DistrictRiskScore)
        .filter(DistrictRiskScore.district_id == district_id)
        .order_by(DistrictRiskScore.date.desc())
        .limit(limit)
        .all()
    )
    return [_enrich(s, db) for s in reversed(scores)]
