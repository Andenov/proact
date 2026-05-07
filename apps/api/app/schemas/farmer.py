from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class FarmerCreate(BaseModel):
    full_name: Optional[str] = None
    phone_number: str
    district_id: Optional[int] = None
    preferred_language: str = "en"
    consent_status: bool = True


class FarmerOut(BaseModel):
    id: int
    full_name: Optional[str] = None
    phone_number: str
    district_id: Optional[int] = None
    district_name: Optional[str] = None
    preferred_language: str
    consent_status: bool
    created_at: datetime

    model_config = {"from_attributes": True}
