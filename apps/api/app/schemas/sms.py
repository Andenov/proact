from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel


class SMSSendRequest(BaseModel):
    district_id: int
    alert_type: str  # flood / landslide / food_stress
    severity: str    # Low / Medium / High
    alert_id: Optional[int] = None


class SMSLogOut(BaseModel):
    id: int
    farmer_id: Optional[int] = None
    district_id: Optional[int] = None
    district_name: Optional[str] = None
    alert_id: Optional[int] = None
    phone_number: str
    message: Optional[str] = None
    provider: Optional[str] = None
    delivery_status: Optional[str] = None
    sent_at: datetime
    provider_response: Optional[Dict[str, Any]] = None

    model_config = {"from_attributes": True}
