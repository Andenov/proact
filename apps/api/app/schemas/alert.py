from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class AlertOut(BaseModel):
    id: int
    district_id: int
    district_name: Optional[str] = None
    alert_type: Optional[str] = None
    severity: Optional[str] = None
    title: Optional[str] = None
    message: Optional[str] = None
    recommended_action: Optional[str] = None
    issued_at: datetime
    status: Optional[str] = None

    model_config = {"from_attributes": True}


class AlertCreate(BaseModel):
    district_id: int
    alert_type: str
    severity: str
    title: str
    message: str
    recommended_action: str
