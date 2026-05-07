from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, Text

from app.db.base import Base


class HazardStaticFeature(Base):
    __tablename__ = "hazard_static_features"

    id = Column(Integer, primary_key=True, index=True)
    district_id = Column(Integer, ForeignKey("districts.id"), unique=True, nullable=False)
    slope_index = Column(Float, default=0.0)
    elevation_mean = Column(Float, default=0.0)
    river_proximity_score = Column(Float, default=0.0)
    floodplain_score = Column(Float, default=0.0)
    landslide_baseline_score = Column(Float, default=0.0)
    rainfall_monthly_avg_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
