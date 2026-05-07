from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String

from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(150))
    email = Column(String(200), unique=True, nullable=False, index=True)
    password_hash = Column(String(255))
    role = Column(String(30), default="viewer")  # admin / analyst / viewer
    organization = Column(String(150))
    created_at = Column(DateTime, default=datetime.utcnow)
