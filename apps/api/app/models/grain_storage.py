from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String

from app.db.base import Base


class GrainStorageUnit(Base):
    __tablename__ = "grain_storage_units"

    id = Column(Integer, primary_key=True, index=True)
    farmer_id = Column(Integer, ForeignKey("farmers.id"), nullable=False, index=True)
    district_id = Column(Integer, ForeignKey("districts.id"), nullable=True, index=True)
    unit_name = Column(String(100), nullable=False)
    hermetic_type = Column(String(50), default="metal_silo")  # metal_silo, pics_bag, sealed_drum
    capacity_kg = Column(Float)
    grain_type = Column(String(50), default="maize")
    subscription_tier = Column(String(20), default="basic")  # basic / premium
    install_date = Column(DateTime)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
