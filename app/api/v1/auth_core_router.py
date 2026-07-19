from __future__ import annotations

from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.domains.auth_core.dependencies import (
    get_auth_claims,
    get_auth_repository,
)
from app.domains.auth_core.login_flow import authenticate_and_issue_tokens
from app.domains.auth_core.repository import (
    AuthenticationCoreRepository,
)
from app.domains.auth_core.schemas import (
    EmailVerificationConfirmRequest,
    EmailVerificationIssueRequest,
    LoginRequest,
    MessageResponse,
    PasswordResetConfirmRequest,
    PasswordResetIssueRequest,
    RefreshRequest,
    SessionResponse,
    TokenPairResponse,
)
from app.domains.auth_core.service import (
    AuthenticationCoreError,
    AuthenticationCoreService,
)
from app.domains.auth_core.types import (
    AuthContext,
    AuthTokenPurpose,
)
from app.domains.email.factory import get_email_provider
from app.domains.email.provider import EmailProvider
from app.domains.identity.repository import UserRepository
from app.domains.rate_limits.rate_limit_service import RateLimitService


# CLIENT-002f: module-level so the in-memory sliding-window counters persist
# across requests within the process (a per-request instance would never
# accumulate usage, defeating the limit) -- same pattern as
# app/api/v1/rate_limit_router.py's module-level _service.
_password_reset_rate_limiter = RateLimitService()


router = APIRouter(
    prefix="/auth",
    tags=["authentication-core"],
)


def request_context(
    request: Request,
) -> AuthContext:
    return AuthContext(
        ip_address=(
            request.client.host
            if request.client
            else None
        ),
        user_agent=request.headers.get(
            "user-agent"
        ),
        device_name=request.headers.get(
            "x-device-name"
        ),
        correlation_id=request.headers.get(
            "x-correlation-id"
        ),
    )


def get_auth_service(
    db: AsyncSession = Depends(get_db),
) -> AuthenticationCoreService:
    # identity.AuthService hashes/verifies via the same app.core.security
    # functions, so passwords set through /identity/register remain
    # verifiable here (see app.domains.auth_core.dependencies.build_auth_service).
    from app.domains.auth_core.dependencies import build_auth_service

    return build_auth_service(db)


def raise_auth_error(
    exc: AuthenticationCoreError,
) -> None:
    raise HTTPException(
        status_code=exc.status_code,
        detail=exc.code,
    ) from exc


@router.post(
    "/login",
    response_model=TokenPairResponse,
    operation_id="auth_core_login",
)
async def login(
    payload: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    service: AuthenticationCoreService = Depends(
        get_auth_service
    ),
):
    context = request_context(request)
    if payload.device_name:
        context = AuthContext(
            ip_address=context.ip_address,
            user_agent=context.user_agent,
            device_name=payload.device_name,
            correlation_id=context.correlation_id,
        )

    try:
        pair = await authenticate_and_issue_tokens(
            identifier=payload.identifier,
            password=payload.password,
            context=context,
            user_repository=UserRepository(db),
            auth_service=service,
        )
    except AuthenticationCoreError as exc:
        raise_auth_error(exc)

    return TokenPairResponse(**pair.__dict__)


@router.post(
    "/refresh",
    response_model=TokenPairResponse,
    operation_id="rotate_auth_refresh_token",
)
async def refresh(
    payload: RefreshRequest,
    request: Request,
    service: AuthenticationCoreService = Depends(
        get_auth_service
    ),
):
    try:
        pair = await service.rotate_refresh_token(
            raw_refresh_token=(
                payload.refresh_token
            ),
            context=request_context(request),
        )
    except AuthenticationCoreError as exc:
        raise_auth_error(exc)

    return TokenPairResponse(
        **pair.__dict__
    )


@router.get(
    "/sessions",
    response_model=list[SessionResponse],
    operation_id="list_current_user_sessions",
)
async def sessions(
    claims: dict = Depends(get_auth_claims),
    repository: AuthenticationCoreRepository = Depends(
        get_auth_repository
    ),
):
    return await repository.list_active_sessions(
        UUID(claims["sub"]),
        now=AuthenticationCoreService.now(),
    )


@router.delete(
    "/sessions/{session_id}",
    response_model=MessageResponse,
    operation_id="revoke_current_user_session",
)
async def revoke_session(
    session_id: UUID,
    request: Request,
    claims: dict = Depends(get_auth_claims),
    service: AuthenticationCoreService = Depends(
        get_auth_service
    ),
):
    revoked = await service.revoke_session(
        user_id=UUID(claims["sub"]),
        session_id=session_id,
        context=request_context(request),
    )

    if not revoked:
        raise HTTPException(
            status_code=404,
            detail="SESSION_NOT_FOUND",
        )

    return MessageResponse(
        success=True,
        message="SESSION_REVOKED",
    )


@router.delete(
    "/sessions",
    response_model=MessageResponse,
    operation_id="revoke_all_current_user_sessions",
)
async def revoke_all_sessions(
    request: Request,
    claims: dict = Depends(get_auth_claims),
    service: AuthenticationCoreService = Depends(
        get_auth_service
    ),
):
    await service.revoke_all_sessions(
        user_id=UUID(claims["sub"]),
        context=request_context(request),
    )
    return MessageResponse(
        success=True,
        message="ALL_SESSIONS_REVOKED",
    )


@router.post(
    "/email-verification/issue",
    response_model=MessageResponse,
    operation_id="issue_email_verification_token",
)
async def issue_email_verification(
    payload: EmailVerificationIssueRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    service: AuthenticationCoreService = Depends(
        get_auth_service
    ),
):
    user = await UserRepository(db).get_by_id(
        str(payload.user_id)
    )
    if user is None:
        raise HTTPException(
            status_code=404,
            detail="USER_NOT_FOUND",
        )

    await service.issue_purpose_token(
        user_id=payload.user_id,
        purpose=(
            AuthTokenPurpose
            .EMAIL_VERIFICATION
        ),
        context=request_context(request),
        lifetime_minutes=60,
    )

    return MessageResponse(
        success=True,
        message="EMAIL_VERIFICATION_ISSUED",
    )


@router.post(
    "/email-verification/confirm",
    response_model=MessageResponse,
    operation_id="confirm_email_verification",
)
async def confirm_email_verification(
    payload: EmailVerificationConfirmRequest,
    request: Request,
    service: AuthenticationCoreService = Depends(
        get_auth_service
    ),
):
    try:
        await service.confirm_email_verification(
            raw_token=payload.token,
            context=request_context(request),
        )
    except AuthenticationCoreError as exc:
        raise_auth_error(exc)

    return MessageResponse(
        success=True,
        message="EMAIL_VERIFIED",
    )


@router.post(
    "/password-reset/issue",
    response_model=MessageResponse,
    operation_id="issue_password_reset_token",
)
async def issue_password_reset(
    payload: PasswordResetIssueRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    service: AuthenticationCoreService = Depends(
        get_auth_service
    ),
    email_provider: EmailProvider = Depends(
        get_email_provider
    ),
):
    # CLIENT-002f (closes the AUTH-000 finding: this endpoint used to be a
    # pure stub that never looked anything up or sent anything). Real
    # token-issuance + email dispatch, still an enumeration-safe boundary --
    # the response is IDENTICAL whether or not the identifier belongs to a
    # real user; only the internal branch differs (real token+email vs
    # nothing at all). Timing-based enumeration (not response-body-based)
    # is an accepted, out-of-scope residual risk -- see WIKI_ROOT ADR-013.
    normalized = payload.identifier.strip().casefold()
    rate_limit_key = f"{request.client.host if request.client else 'unknown'}:{normalized}"
    rate_limit = _password_reset_rate_limiter.check(
        {"key": rate_limit_key, "scope": "password_reset"}
    )
    if not rate_limit["allowed"]:
        raise HTTPException(
            status_code=429,
            detail="PASSWORD_RESET_RATE_LIMITED",
        )

    user = await UserRepository(db).get_by_email(payload.identifier)
    if user is not None:
        raw_token = await service.issue_purpose_token(
            user_id=user.id,
            purpose=AuthTokenPurpose.PASSWORD_RESET,
            context=request_context(request),
            lifetime_minutes=settings.PASSWORD_RESET_TOKEN_MINUTES,
        )
        reset_link = (
            f"{settings.FRONTEND_ORIGIN}/{user.preferred_language}"
            f"/sifre-sifirla?token={raw_token}"
        )
        await email_provider.send(
            to=user.email,
            subject="Reset your password",
            body=(
                "Someone (hopefully you) requested a password reset.\n"
                f"Reset link (valid {settings.PASSWORD_RESET_TOKEN_MINUTES} "
                f"minutes, single use): {reset_link}\n"
                "If you didn't request this, you can ignore this email."
            ),
        )

    return MessageResponse(
        success=True,
        message=(
            "PASSWORD_RESET_REQUEST_ACCEPTED"
        ),
    )


@router.post(
    "/password-reset/confirm",
    response_model=MessageResponse,
    operation_id="confirm_password_reset",
)
async def confirm_password_reset(
    payload: PasswordResetConfirmRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    service: AuthenticationCoreService = Depends(
        get_auth_service
    ),
):
    # CLIENT-002f: previously 404 (route didn't exist at all -- AUTH-000
    # finding). complete_password_reset() itself already existed, fully
    # implemented (single-use + expiring token consumption, password
    # policy/history checks, security_version bump that invalidates
    # existing JWTs, session revocation) -- it was simply never wired to a
    # route.
    user_repository = UserRepository(db)

    async def _set_password_hash(user_id, new_hash: str) -> None:
        await user_repository.set_password_hash(user_id, new_hash)

    try:
        await service.complete_password_reset(
            raw_token=payload.token,
            new_password=payload.new_password,
            identity_fragments=(),
            set_user_password_hash=_set_password_hash,
            context=request_context(request),
        )
    except AuthenticationCoreError as exc:
        raise_auth_error(exc)

    return MessageResponse(
        success=True,
        message="PASSWORD_RESET_COMPLETED",
    )
