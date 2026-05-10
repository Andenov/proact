from datetime import date, datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.models.district import District
from app.models.farmer import Farmer
from app.models.grain_storage import GrainStorageUnit
from app.models.silo_reading import SiloReading
from app.models.storage_risk import StorageRiskScore
from app.schemas.storage import SiloReadingCreate, StorageUnitCreate
from app.services.storage_risk_engine import compute_aflatoxin_score

router = APIRouter(prefix="/storage", tags=["storage"])


def _enrich_unit(unit: GrainStorageUnit, db: Session) -> Dict[str, Any]:
    farmer = db.query(Farmer).filter(Farmer.id == unit.farmer_id).first()
    district = db.query(District).filter(District.id == unit.district_id).first() if unit.district_id else None
    latest_risk = (
        db.query(StorageRiskScore)
        .filter(StorageRiskScore.unit_id == unit.id)
        .order_by(StorageRiskScore.date.desc())
        .first()
    )
    latest_reading = (
        db.query(SiloReading)
        .filter(SiloReading.unit_id == unit.id)
        .order_by(SiloReading.timestamp.desc())
        .first()
    )
    return {
        "id": unit.id,
        "farmer_id": unit.farmer_id,
        "farmer_name": farmer.full_name if farmer else None,
        "district_id": unit.district_id,
        "district_name": district.name if district else None,
        "unit_name": unit.unit_name,
        "hermetic_type": unit.hermetic_type,
        "capacity_kg": unit.capacity_kg,
        "grain_type": unit.grain_type,
        "subscription_tier": unit.subscription_tier,
        "install_date": unit.install_date.date().isoformat() if unit.install_date else None,
        "is_active": unit.is_active,
        "created_at": unit.created_at.isoformat() if unit.created_at else None,
        "latest_risk": {
            "score": latest_risk.aflatoxin_score,
            "level": latest_risk.level,
            "predicted_days_safe": latest_risk.predicted_days_safe,
            "recommendation": latest_risk.recommendation,
        } if latest_risk else None,
        "latest_reading": {
            "timestamp": latest_reading.timestamp.isoformat() if latest_reading.timestamp else None,
            "moisture_pct": latest_reading.moisture_pct,
            "temp_c": latest_reading.temp_c,
            "humidity_pct": latest_reading.humidity_pct,
            "co2_ppm": latest_reading.co2_ppm,
        } if latest_reading else None,
    }


def _run_risk(unit: GrainStorageUnit, reading: SiloReading, db: Session) -> Dict[str, Any]:
    install_date = unit.install_date or unit.created_at
    days_sealed = (datetime.utcnow() - install_date).days if install_date else 0
    return compute_aflatoxin_score(
        moisture_pct=reading.moisture_pct or 12.0,
        temp_c=reading.temp_c or 28.0,
        humidity_pct=reading.humidity_pct or 65.0,
        co2_ppm=reading.co2_ppm or 600.0,
        days_sealed=days_sealed,
    )


@router.get("/units", response_model=List[Dict[str, Any]])
def list_units(
    farmer_id: Optional[int] = Query(None),
    district_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
):
    q = db.query(GrainStorageUnit).filter(GrainStorageUnit.is_active == True)
    if farmer_id:
        q = q.filter(GrainStorageUnit.farmer_id == farmer_id)
    if district_id:
        q = q.filter(GrainStorageUnit.district_id == district_id)
    return [_enrich_unit(u, db) for u in q.order_by(GrainStorageUnit.created_at.desc()).all()]


@router.post("/units", response_model=Dict[str, Any])
def register_unit(payload: StorageUnitCreate, db: Session = Depends(get_db)):
    if not db.query(Farmer).filter(Farmer.id == payload.farmer_id).first():
        raise HTTPException(status_code=404, detail="Farmer not found")
    unit = GrainStorageUnit(**payload.model_dump())
    db.add(unit)
    db.commit()
    db.refresh(unit)
    return _enrich_unit(unit, db)


@router.get("/units/{unit_id}", response_model=Dict[str, Any])
def get_unit(unit_id: int, db: Session = Depends(get_db)):
    unit = db.query(GrainStorageUnit).filter(GrainStorageUnit.id == unit_id).first()
    if not unit:
        raise HTTPException(status_code=404, detail="Storage unit not found")
    return _enrich_unit(unit, db)


@router.post("/units/{unit_id}/readings", response_model=Dict[str, Any])
def submit_reading(unit_id: int, payload: SiloReadingCreate, db: Session = Depends(get_db)):
    unit = db.query(GrainStorageUnit).filter(GrainStorageUnit.id == unit_id).first()
    if not unit:
        raise HTTPException(status_code=404, detail="Storage unit not found")

    reading = SiloReading(
        unit_id=unit_id,
        timestamp=payload.timestamp or datetime.utcnow(),
        temp_c=payload.temp_c,
        moisture_pct=payload.moisture_pct,
        humidity_pct=payload.humidity_pct,
        co2_ppm=payload.co2_ppm,
    )
    db.add(reading)
    db.flush()

    result = _run_risk(unit, reading, db)

    # Upsert today's risk score
    existing = (
        db.query(StorageRiskScore)
        .filter(StorageRiskScore.unit_id == unit_id, StorageRiskScore.date == date.today())
        .first()
    )
    if existing:
        existing.aflatoxin_score = result["score"]
        existing.level = result["level"]
        existing.predicted_days_safe = result["predicted_days_safe"]
        existing.top_drivers_json = result["top_drivers"]
        existing.recommendation = result["recommendations"][0]
    else:
        db.add(StorageRiskScore(
            unit_id=unit_id,
            date=date.today(),
            aflatoxin_score=result["score"],
            level=result["level"],
            predicted_days_safe=result["predicted_days_safe"],
            top_drivers_json=result["top_drivers"],
            recommendation=result["recommendations"][0],
        ))

    db.commit()
    return {
        "reading_id": reading.id,
        "risk": {
            "score": result["score"],
            "level": result["level"],
            "predicted_days_safe": result["predicted_days_safe"],
            "description": result["description"],
            "recommendations": result["recommendations"],
        },
    }


@router.get("/units/{unit_id}/readings", response_model=List[Dict[str, Any]])
def get_readings(unit_id: int, limit: int = Query(20, ge=1, le=100), db: Session = Depends(get_db)):
    rows = (
        db.query(SiloReading)
        .filter(SiloReading.unit_id == unit_id)
        .order_by(SiloReading.timestamp.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": r.id,
            "timestamp": r.timestamp.isoformat() if r.timestamp else None,
            "temp_c": r.temp_c,
            "moisture_pct": r.moisture_pct,
            "humidity_pct": r.humidity_pct,
            "co2_ppm": r.co2_ppm,
        }
        for r in rows
    ]


@router.get("/units/{unit_id}/risk", response_model=Dict[str, Any])
def get_unit_risk(unit_id: int, db: Session = Depends(get_db)):
    risk = (
        db.query(StorageRiskScore)
        .filter(StorageRiskScore.unit_id == unit_id)
        .order_by(StorageRiskScore.date.desc())
        .first()
    )
    if not risk:
        raise HTTPException(status_code=404, detail="No risk scores for this unit")
    return {
        "unit_id": unit_id,
        "date": str(risk.date),
        "score": risk.aflatoxin_score,
        "level": risk.level,
        "predicted_days_safe": risk.predicted_days_safe,
        "top_drivers": risk.top_drivers_json,
        "recommendation": risk.recommendation,
    }


@router.post("/compute-risk", response_model=Dict[str, Any])
def compute_all_risks(db: Session = Depends(get_db)):
    """Recompute risk for all active units from their latest reading."""
    units = db.query(GrainStorageUnit).filter(GrainStorageUnit.is_active == True).all()
    computed = 0
    for unit in units:
        latest = (
            db.query(SiloReading)
            .filter(SiloReading.unit_id == unit.id)
            .order_by(SiloReading.timestamp.desc())
            .first()
        )
        if not latest:
            continue
        result = _run_risk(unit, latest, db)
        existing = (
            db.query(StorageRiskScore)
            .filter(StorageRiskScore.unit_id == unit.id, StorageRiskScore.date == date.today())
            .first()
        )
        if existing:
            existing.aflatoxin_score = result["score"]
            existing.level = result["level"]
            existing.predicted_days_safe = result["predicted_days_safe"]
            existing.top_drivers_json = result["top_drivers"]
            existing.recommendation = result["recommendations"][0]
        else:
            db.add(StorageRiskScore(
                unit_id=unit.id,
                date=date.today(),
                aflatoxin_score=result["score"],
                level=result["level"],
                predicted_days_safe=result["predicted_days_safe"],
                top_drivers_json=result["top_drivers"],
                recommendation=result["recommendations"][0],
            ))
        computed += 1
    db.commit()
    return {"computed": computed}
