from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class DistrictBase(BaseModel):
    name: str
    region: Optional[str] = None
    country: str = "Uganda"
    centroid_lat: Optional[float] = None
    centroid_lon: Optional[float] = None
    slope_index: float = 0.0
    flood_exposure_index: float = 0.0


class DistrictOut(DistrictBase):
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}


class DistrictWithRisk(DistrictOut):
    flood_score: Optional[float] = None
    flood_level: Optional[str] = None
    landslide_score: Optional[float] = None
    landslide_level: Optional[str] = None
    food_stress_score: Optional[float] = None
    food_stress_level: Optional[str] = None
