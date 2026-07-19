from __future__ import annotations

from fastapi import Depends, HTTPException, Request
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.security import hash_password, verify_password
from app.domains.auth_core.password_policy import PasswordPolicy
from app.domains.auth_core.repository import (
    AuthenticationCoreRepository,
)
from app.domains.auth_core.service import AuthenticationCoreService
from app.domains.auth_core.tokens import (
    TokenCodec,
    TokenValidationError,
)


bearer_scheme = HTTPBearer(
    auto_error=False
)


def get_token_codec() -> TokenCodec:
    return TokenCodec(
        secret=settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
        issuer=getattr(
            settings,
            "JWT_ISSUER",
            "ai-consumer-intelligence",
        ),
        audience=getattr(
            settings,
            "JWT_AUDIENCE",
            "ai-consumer-intelligence-api",
        ),
        access_minutes=(
            settings.ACCESS_TOKEN_EXPIRE_MINUTES
        ),
    )


def get_auth_repository(
    session: AsyncSession = Depends(get_db),
) -> AuthenticationCoreRepository:
    return AuthenticationCoreRepository(
        session
    )


def build_auth_service(
    session: AsyncSession,
) -> AuthenticationCoreService:
    """Single construction path for AuthenticationCoreService.

    Used by both /auth/login (auth_core_router) and /identity/login
    (identity/router, delegating) so the two login endpoints share one
    lockout/password-policy configuration instead of drifting apart.
    """
    return AuthenticationCoreService(
        AuthenticationCoreRepository(session),
        token_codec=get_token_codec(),
        password_policy=PasswordPolicy(),
        password_verifier=verify_password,
        password_hasher=hash_password,
        access_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        refresh_days=settings.REFRESH_TOKEN_EXPIRE_DAYS,
        session_days=settings.AUTH_SESSION_EXPIRE_DAYS,
        maximum_failed_attempts=settings.AUTH_MAX_FAILED_ATTEMPTS,
        lockout_minutes=settings.AUTH_LOCKOUT_MINUTES,
    )


async def get_auth_claims(
    credentials: HTTPAuthorizationCredentials
    | None = Depends(bearer_scheme),
    codec: TokenCodec = Depends(
        get_token_codec
    ),
) -> dict:
    if credentials is None:
        raise HTTPException(
            status_code=401,
            detail="AUTHENTICATION_REQUIRED",
        )

    try:
        return codec.decode_access_token(
            credentials.credentials
        )
    except TokenValidationError as exc:
        raise HTTPException(
            status_code=401,
            detail=str(exc),
        ) from exc
