"""Application schemas."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr


class ApplicationCreate(BaseModel):
    username: str
    email: EmailStr
    reason: Optional[str] = None


class ApplicationResponse(BaseModel):
    id: int
    user_id: int
    reason: Optional[str] = None
    status: str
    created_at: datetime
    reviewed_at: Optional[datetime] = None
    user_username: Optional[str] = None
    user_email: Optional[str] = None

    class Config:
        from_attributes = True


class ApplicationListResponse(BaseModel):
    items: list[ApplicationResponse]
    total: int
