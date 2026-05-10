from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer

from app.db.base import Base


class SiloReading(Base):
    __tablename__ = "silo_readings"

    id = Column(Integer, primary_key=True, index=True)
    unit_id = Column(Integer, ForeignKey("grain_storage_units.id"), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    temp_c = Column(Float)
    moisture_pct = Column(Float)
    humidity_pct = Column(Float)
    co2_ppm = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
