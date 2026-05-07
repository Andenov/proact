from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.models.district import District
from app.models.farmer import Farmer
from app.schemas.farmer import FarmerCreate, FarmerOut

router = APIRouter(prefix="/farmers", tags=["farmers"])


def _enrich(farmer: Farmer, db: Session) -> FarmerOut:
    out = FarmerOut.model_validate(farmer)
    if farmer.district_id:
        district = db.query(District).filter(District.id == farmer.district_id).first()
        out.district_name = district.name if district else None
    return out


@router.get("", response_model=List[FarmerOut])
def list_farmers(
    district_id: Optional[int] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    q = db.query(Farmer).order_by(Farmer.created_at.desc())
    if district_id:
        q = q.filter(Farmer.district_id == district_id)
    farmers = q.limit(limit).all()
    return [_enrich(f, db) for f in farmers]


@router.post("", response_model=FarmerOut)
def register_farmer(payload: FarmerCreate, db: Session = Depends(get_db)):
    farmer = Farmer(**payload.model_dump())
    db.add(farmer)
    db.commit()
    db.refresh(farmer)
    return _enrich(farmer, db)


@router.get("/{farmer_id}", response_model=FarmerOut)
def get_farmer(farmer_id: int, db: Session = Depends(get_db)):
    farmer = db.query(Farmer).filter(Farmer.id == farmer_id).first()
    if not farmer:
        raise HTTPException(status_code=404, detail="Farmer not found")
    return _enrich(farmer, db)
