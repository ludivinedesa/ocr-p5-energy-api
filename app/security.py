"""API-key authentication for protected endpoints."""

from hmac import compare_digest
from typing import Optional

from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

from app.config import API_KEY


api_key_header = APIKeyHeader(
    name="X-API-Key",
    auto_error=False,
)


def require_api_key(
    provided_api_key: Optional[str] = Security(api_key_header),
) -> str:
    """Validate the API key supplied in the X-API-Key header."""
    if not API_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="API authentication is not configured.",
        )

    if (
        provided_api_key is None
        or not compare_digest(provided_api_key, API_KEY)
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key.",
        )

    return provided_api_key
