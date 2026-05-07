from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    full_name: Optional[str] = None
    email: str
    password: str
    role: str = "viewer"
    organization: Optional[str] = None


class UserOut(BaseModel):
    id: int
    full_name: Optional[str] = None
    email: str
    role: str
    organization: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut
