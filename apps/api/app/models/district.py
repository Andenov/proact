from datetime import datetime

from geoalchemy2 import Geometry
from sqlalchemy import Column, DateTime, Float, Integer, String, func

from app.db.base import Base


class District(Base):
    __tablename__ = "districts"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    region = Column(String(100))
    country = Column(String(50), default="Uganda")
    geometry = Column(Geometry("MULTIPOLYGON", srid=4326), nullable=True)
    centroid_lat = Column(Float)
    centroid_lon = Column(Float)
    slope_index = Column(Float, default=0.0)
    flood_exposure_index = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
