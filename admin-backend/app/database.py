"""Database engine and session management."""
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker, Session

from app.config import get_settings

settings = get_settings()

# SQLite needs this for FK and async-friendly usage in some setups
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    echo=bool(__debug__),  # SQL echo in dev if needed
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db() -> Session:
    """Dependency that yields a DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create all tables. Call on startup if not using migrations."""
    from app.models import User, ApiKeyApplication, ApiCredential  # noqa: F401
    Base.metadata.create_all(bind=engine)
    # Minimal migration: add token_balance to api_credentials if missing (e.g. existing SQLite DB)
    if settings.DATABASE_URL.startswith("sqlite"):
        with engine.connect() as conn:
            r = conn.execute(text("PRAGMA table_info(api_credentials)"))
            rows = r.fetchall()
            if rows and not any(row[1] == "token_balance" for row in rows):
                conn.execute(text(
                    "ALTER TABLE api_credentials ADD COLUMN token_balance INTEGER NOT NULL DEFAULT 0"
                ))
                conn.commit()
            if rows and not any(row[1] == "tokens_used" for row in rows):
                conn.execute(text(
                    "ALTER TABLE api_credentials ADD COLUMN tokens_used INTEGER NOT NULL DEFAULT 0"
                ))
                conn.commit()
