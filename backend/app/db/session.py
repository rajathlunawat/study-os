"""
StudyOS DB — Session management.

Synchronous SQLAlchemy setup for SQLite.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings

_settings = get_settings()

engine = create_engine(
    _settings.DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=_settings.DEBUG,
)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)

def get_db() -> Session:  # type: ignore[misc]
    """Yield a database session and ensure cleanup."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
