from __future__ import annotations

from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
)
from sqlalchemy.ext.asyncio import AsyncSession

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
from app.domains.identity.repository import UserRepository


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
):
    # Enumeration-safe boundary. Wire the actual identity lookup and
    # delivery adapter in the integration patch.
    return MessageResponse(
        success=True,
        message=(
            "PASSWORD_RESET_REQUEST_ACCEPTED"
        ),
    )
