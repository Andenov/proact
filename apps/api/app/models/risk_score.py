from datetime import datetime

from sqlalchemy import JSON, Column, Date, DateTime, Float, ForeignKey, Integer, String

from app.db.base import Base


class DistrictRiskScore(Base):
    __tablename__ = "district_risk_scores"

    id = Column(Integer, primary_key=True, index=True)
    district_id = Column(Integer, ForeignKey("districts.id"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    flood_score = Column(Float, default=0.0)
    flood_level = Column(String(10))
    landslide_score = Column(Float, default=0.0)
    landslide_level = Column(String(10))
    food_stress_score = Column(Float, default=0.0)
    food_stress_level = Column(String(10))
    top_drivers_json = Column(JSON)
    recommendations_json = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
