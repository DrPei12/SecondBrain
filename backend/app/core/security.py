"""
API key authentication helpers.
"""
from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

from app.core.config import settings


api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def require_api_key(api_key: str | None = Security(api_key_header)) -> None:
    """Require the configured API key for private knowledge APIs."""
    expected_key = settings.SECOND_BRAIN_API_KEY.strip()
    if not expected_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="SECOND_BRAIN_API_KEY is not configured",
        )

    if api_key != expected_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        )
