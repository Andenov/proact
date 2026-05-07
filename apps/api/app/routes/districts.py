from typing import List, Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.models.district import District
from app.models.risk_score import DistrictRiskScore
from app.schemas.district import DistrictOut, DistrictWithRisk

router = APIRouter(prefix="/districts", tags=["districts"])


@router.get("", response_model=List[DistrictWithRisk])
def list_districts(db: Session = Depends(get_db)):
    districts = db.query(District).all()
    result = []
    for d in districts:
        latest_score = (
            db.query(DistrictRiskScore)
            .filter(DistrictRiskScore.district_id == d.id)
            .order_by(DistrictRiskScore.date.desc())
            .first()
        )
        row = DistrictWithRisk.model_validate(d)
        if latest_score:
            row.flood_score = latest_score.flood_score
            row.flood_level = latest_score.flood_level
            row.landslide_score = latest_score.landslide_score
            row.landslide_level = latest_score.landslide_level
            row.food_stress_score = latest_score.food_stress_score
            row.food_stress_level = latest_score.food_stress_level
        result.append(row)
    return result


@router.get("/{district_id}", response_model=DistrictWithRisk)
def get_district(district_id: int, db: Session = Depends(get_db)):
    from fastapi import HTTPException
    d = db.query(District).filter(District.id == district_id).first()
    if not d:
        raise HTTPException(status_code=404, detail="District not found")
    latest_score = (
        db.query(DistrictRiskScore)
        .filter(DistrictRiskScore.district_id == d.id)
        .order_by(DistrictRiskScore.date.desc())
        .first()
    )
    row = DistrictWithRisk.model_validate(d)
    if latest_score:
        row.flood_score = latest_score.flood_score
        row.flood_level = latest_score.flood_level
        row.landslide_score = latest_score.landslide_score
        row.landslide_level = latest_score.landslide_level
        row.food_stress_score = latest_score.food_stress_score
        row.food_stress_level = latest_score.food_stress_level
    return row
