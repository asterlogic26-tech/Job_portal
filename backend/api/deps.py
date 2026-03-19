from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from backend.db.session import get_db
from backend.core.config import settings
import uuid


async def get_session(db: AsyncSession = Depends(get_db)) -> AsyncSession:
    return db


def get_user_id() -> uuid.UUID:
    """Single-user system — always returns the fixed user ID."""
    return uuid.UUID(settings.single_user_id)
