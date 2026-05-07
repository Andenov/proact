from datetime import datetime

from sqlalchemy import Column, Date, DateTime, Float, ForeignKey, Integer, String

from app.db.base import Base


class WeatherObservation(Base):
    __tablename__ = "weather_observations"

    id = Column(Integer, primary_key=True, index=True)
    district_id = Column(Integer, ForeignKey("districts.id"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    rainfall_mm = Column(Float)
    tmin_c = Column(Float)
    tmax_c = Column(Float)
    soil_moisture = Column(Float, nullable=True)
    anomaly_score = Column(Float, default=0.0)
    source = Column(String(50), default="open-meteo")
    created_at = Column(DateTime, default=datetime.utcnow)
