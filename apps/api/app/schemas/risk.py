from datetime import date, datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class RiskScoreOut(BaseModel):
    id: int
    district_id: int
    district_name: Optional[str] = None
    date: date
    flood_score: Optional[float] = None
    flood_level: Optional[str] = None
    landslide_score: Optional[float] = None
    landslide_level: Optional[str] = None
    food_stress_score: Optional[float] = None
    food_stress_level: Optional[str] = None
    top_drivers_json: Optional[Dict[str, Any]] = None
    recommendations_json: Optional[Dict[str, Any]] = None
    created_at: datetime

    model_config = {"from_attributes": True}
