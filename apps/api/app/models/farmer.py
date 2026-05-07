from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String

from app.db.base import Base


class Farmer(Base):
    __tablename__ = "farmers"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(150))
    phone_number = Column(String(20), nullable=False, index=True)
    district_id = Column(Integer, ForeignKey("districts.id"), nullable=True, index=True)
    preferred_language = Column(String(20), default="en")
    consent_status = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
