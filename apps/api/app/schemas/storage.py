from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class StorageUnitCreate(BaseModel):
    farmer_id: int
    district_id: Optional[int] = None
    unit_name: str
    hermetic_type: str = "metal_silo"
    capacity_kg: Optional[float] = None
    grain_type: str = "maize"
    subscription_tier: str = "basic"
    install_date: Optional[datetime] = None


class SiloReadingCreate(BaseModel):
    temp_c: Optional[float] = None
    moisture_pct: Optional[float] = None
    humidity_pct: Optional[float] = None
    co2_ppm: Optional[float] = None
    timestamp: Optional[datetime] = None
