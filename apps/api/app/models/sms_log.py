from datetime import datetime

from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, String, Text

from app.db.base import Base


class SMSLog(Base):
    __tablename__ = "sms_logs"

    id = Column(Integer, primary_key=True, index=True)
    farmer_id = Column(Integer, ForeignKey("farmers.id"), nullable=True)
    district_id = Column(Integer, ForeignKey("districts.id"), nullable=True, index=True)
    alert_id = Column(Integer, ForeignKey("alerts.id"), nullable=True)
    phone_number = Column(String(20), nullable=False)
    message = Column(Text)
    provider = Column(String(50), default="mock")
    delivery_status = Column(String(30), default="queued", index=True)
    sent_at = Column(DateTime, default=datetime.utcnow)
    provider_response = Column(JSON)
