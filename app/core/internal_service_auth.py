from fastapi import Header, HTTPException, status

from app.core.config import settings


def require_internal_service_key(
    x_internal_service_key: str | None = Header(default=None),
) -> None:
    """AUTH-004 (ADR-006): guards INTERNAL_SERVICE-classified endpoints
    (connector/ingestion/storage-worker internals) with a shared secret
    instead of user auth -- these are called by other services, not by an
    end user holding a JWT. A missing or mismatched key is 401, same
    semantics as get_current_user's missing/invalid token."""
    if not x_internal_service_key or x_internal_service_key != settings.INTERNAL_SERVICE_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "INVALID_INTERNAL_SERVICE_KEY"},
        )
