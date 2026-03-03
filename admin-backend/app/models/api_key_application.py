"""API Key application model."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
import enum

from app.database import Base


class ApplicationStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class ApiKeyApplication(Base):
    __tablename__ = "api_key_applications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    reason = Column(Text, nullable=True)
    status = Column(
        String(20),
        nullable=False,
        default=ApplicationStatus.PENDING.value,
        index=True,
    )
    created_at = Column(DateTime, default=datetime.utcnow)
    reviewed_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="applications")
    credential = relationship(
        "ApiCredential",
        back_populates="application",
        uselist=False,
    )
