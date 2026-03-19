"""
Minimal security for single-user deployment.
Uses a static API key set in .env for basic auth on sensitive endpoints.
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader
from backend.core.config import settings

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(api_key: str | None = Depends(api_key_header)) -> bool:
    """
    For single-user local deployment, API key is optional.
    If SECRET_KEY is set in env beyond the default, enforce it.
    """
    if settings.secret_key == "change-me-in-production-please":
        # Dev mode — no auth
        return True
    if not api_key or api_key != settings.secret_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or missing API key",
        )
    return True
