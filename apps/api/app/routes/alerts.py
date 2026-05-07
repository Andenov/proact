from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.models.alert import Alert
from app.models.district import District
from app.schemas.alert import AlertCreate, AlertOut
from app.services.alert_service import generate_alerts_from_scores

router = APIRouter(prefix="/alerts", tags=["alerts"])


def _enrich(alert: Alert, db: Session) -> AlertOut:
    out = AlertOut.model_validate(alert)
    district = db.query(District).filter(District.id == alert.district_id).first()
    out.district_name = district.name if district else None
    return out


@router.get("", response_model=List[AlertOut])
def list_alerts(
    status: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    alert_type: Optional[str] = Query(None),
    district_id: Optional[int] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    q = db.query(Alert).order_by(Alert.issued_at.desc())
    if status:
        q = q.filter(Alert.status == status)
    if severity:
        q = q.filter(Alert.severity == severity)
    if alert_type:
        q = q.filter(Alert.alert_type == alert_type)
    if district_id:
        q = q.filter(Alert.district_id == district_id)
    alerts = q.limit(limit).all()
    return [_enrich(a, db) for a in alerts]


@router.post("/generate")
def generate_alerts(db: Session = Depends(get_db)):
    new_alerts = generate_alerts_from_scores(db)
    return {"generated": len(new_alerts), "alerts": [a.id for a in new_alerts]}


@router.post("", response_model=AlertOut)
def create_alert(payload: AlertCreate, db: Session = Depends(get_db)):
    alert = Alert(**payload.model_dump())
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return _enrich(alert, db)
