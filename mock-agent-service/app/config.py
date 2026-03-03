"""配置：从环境变量读取，便于部署与后续替换为真实服务."""
import os
from functools import lru_cache


@lru_cache
def get_settings() -> "Settings":
    return Settings()


class Settings:
    """应用配置."""

    # 数据库（演示用 SQLite；后续可改为 PostgreSQL 等）
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./agent.db")

    # 可选：模拟回复的前缀，便于后续替换为真实 LLM 时保留占位
    MOCK_REPLY_PREFIX: str = os.getenv("MOCK_REPLY_PREFIX", "我是养成式智能体，很高兴和你交流：")

    # Token 扣减：调用 admin-backend 内部接口
    ADMIN_BACKEND_URL: str = os.getenv("ADMIN_BACKEND_URL", "http://127.0.0.1:8000").rstrip("/")
    INTERNAL_SECRET: str = os.getenv("INTERNAL_SECRET", "")
