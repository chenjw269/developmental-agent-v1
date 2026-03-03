"""Common dependencies."""
from typing import Annotated, Generator, Optional

from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db

Settings = get_settings()


def require_admin(
    x_admin_key: Annotated[Optional[str], Header(alias="X-Admin-Key")] = None,
) -> None:
    """Require X-Admin-Key header if ADMIN_API_KEY is set."""
    if not Settings.ADMIN_API_KEY:
        return
    if x_admin_key != Settings.ADMIN_API_KEY:
        raise HTTPException(status_code=403, detail="Admin key required")


def get_db_session() -> Generator[Session, None, None]:
    yield from get_db()
