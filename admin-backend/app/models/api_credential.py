"""API credential (issued key) model."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship

from app.database import Base


class ApiCredential(Base):
    __tablename__ = "api_credentials"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    application_id = Column(Integer, ForeignKey("api_key_applications.id"), nullable=True, index=True)
    consumer_name = Column(String(128), nullable=False, unique=True, index=True)
    api_key = Column(String(256), nullable=False, index=True)
    quota_per_minute = Column(Integer, nullable=False, default=60)
    token_balance = Column(Integer, nullable=False, default=0)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="credentials")
    application = relationship("ApiKeyApplication", back_populates="credential")
