from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.models.district import District
from app.models.farmer import Farmer
from app.models.sms_log import SMSLog
from app.schemas.sms import SMSLogOut, SMSSendRequest
from app.services.sms_service import build_sms_message, get_sms_provider

router = APIRouter(prefix="/sms", tags=["sms"])


@router.post("/send")
def send_sms(payload: SMSSendRequest, db: Session = Depends(get_db)):
    district = db.query(District).filter(District.id == payload.district_id).first()
    if not district:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="District not found")

    farmers = (
        db.query(Farmer)
        .filter(Farmer.district_id == payload.district_id, Farmer.consent_status == True)
        .all()
    )

    if not farmers:
        return {"sent": 0, "message": "No consented farmers in this district"}

    provider = get_sms_provider()
    message = build_sms_message(district.name, payload.alert_type, payload.severity)
    logs = []

    for farmer in farmers:
        result = provider.send(farmer.phone_number, message)
        log = SMSLog(
            farmer_id=farmer.id,
            district_id=payload.district_id,
            alert_id=payload.alert_id,
            phone_number=farmer.phone_number,
            message=message,
            provider=result.get("provider", "mock"),
            delivery_status=result.get("status", "queued"),
            provider_response=result,
        )
        db.add(log)
        logs.append(log)

    db.commit()
    return {"sent": len(logs), "district": district.name, "message_preview": message}


@router.get("/logs", response_model=List[SMSLogOut])
def sms_logs(
    district_id: Optional[int] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    q = db.query(SMSLog).order_by(SMSLog.sent_at.desc())
    if district_id:
        q = q.filter(SMSLog.district_id == district_id)
    logs = q.limit(limit).all()

    result = []
    for log in logs:
        out = SMSLogOut.model_validate(log)
        if log.district_id:
            district = db.query(District).filter(District.id == log.district_id).first()
            out.district_name = district.name if district else None
        result.append(out)
    return result
