from datetime import datetime

from sqlalchemy import JSON, Column, Date, DateTime, Float, ForeignKey, Integer, String

from app.db.base import Base


class StorageRiskScore(Base):
    __tablename__ = "storage_risk_scores"

    id = Column(Integer, primary_key=True, index=True)
    unit_id = Column(Integer, ForeignKey("grain_storage_units.id"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    aflatoxin_score = Column(Float)
    level = Column(String(10))
    predicted_days_safe = Column(Integer)
    top_drivers_json = Column(JSON)
    recommendation = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)
