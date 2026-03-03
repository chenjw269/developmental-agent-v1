"""会话表（可选）：按 consumer + session_id 聚合多轮对话."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime

from app.database import Base


class Session(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    consumer_name = Column(String(128), nullable=False, index=True)
    session_id = Column(String(64), nullable=False, unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
