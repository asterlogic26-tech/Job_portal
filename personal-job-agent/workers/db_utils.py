"""
Synchronous DB utilities for Celery workers.
Workers use sync SQLAlchemy since Celery runs in sync context.
"""
import os
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator

_engine = None
_SessionLocal = None


def get_engine():
    global _engine
    if _engine is None:
        # Use sync URL (no asyncpg)
        db_url = os.environ.get(
            "DATABASE_URL_SYNC",
            os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/job_agent")
        )
        # Convert asyncpg URL to sync
        db_url = db_url.replace("postgresql+asyncpg://", "postgresql://")
        _engine = create_engine(db_url, pool_pre_ping=True, pool_size=5, max_overflow=10)
    return _engine


def get_session_factory():
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(bind=get_engine(), autocommit=False, autoflush=False)
    return _SessionLocal


@contextmanager
def get_sync_session() -> Generator[Session, None, None]:
    """Get a synchronous SQLAlchemy session for use in Celery tasks."""
    SessionLocal = get_session_factory()
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
