"""Application configuration from environment variables."""
import os
from functools import lru_cache
from typing import Optional


@lru_cache
def get_settings() -> "Settings":
    return Settings()


class Settings:
    """Settings loaded from environment."""

    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "sqlite:///./admin.db",
    )

    # APISIX Admin API
    APISIX_ADMIN_URL: str = os.getenv(
        "APISIX_ADMIN_URL",
        "http://127.0.0.1:9180",
    ).rstrip("/")
    APISIX_ADMIN_KEY: Optional[str] = os.getenv("APISIX_ADMIN_KEY")

    # Optional: API key for protecting admin endpoints (same key = admin)
    ADMIN_API_KEY: Optional[str] = os.getenv("ADMIN_API_KEY")

    # Internal API: secret for mock-agent-service to call deduct-token
    INTERNAL_SECRET: Optional[str] = os.getenv("INTERNAL_SECRET")

    # Initial token_balance when approving an application
    INITIAL_TOKEN_BALANCE: int = int(os.getenv("INITIAL_TOKEN_BALANCE", "10"))

    def __init__(self) -> None:
        # Allow override from env after class definition
        self.DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./admin.db")
        self.APISIX_ADMIN_URL = (os.getenv("APISIX_ADMIN_URL", "http://127.0.0.1:9180") or "").rstrip("/")
        self.APISIX_ADMIN_KEY = os.getenv("APISIX_ADMIN_KEY")
        self.ADMIN_API_KEY = os.getenv("ADMIN_API_KEY")
        self.INTERNAL_SECRET = os.getenv("INTERNAL_SECRET")
        self.INITIAL_TOKEN_BALANCE = int(os.getenv("INITIAL_TOKEN_BALANCE", "10"))


# Re-export
SettingsType = Settings
