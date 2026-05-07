from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text

from app.db.base import Base


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    district_id = Column(Integer, ForeignKey("districts.id"), nullable=False, index=True)
    alert_type = Column(String(50), index=True)  # flood / landslide / food_stress
    severity = Column(String(10), index=True)    # Low / Medium / High
    title = Column(String(200))
    message = Column(Text)
    recommended_action = Column(Text)
    issued_at = Column(DateTime, default=datetime.utcnow, index=True)
    status = Column(String(20), default="active")
