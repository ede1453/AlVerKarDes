from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.domains.auth_core.dependencies import build_auth_service
from app.domains.auth_core.login_flow import authenticate_and_issue_tokens
from app.domains.auth_core.service import AuthenticationCoreError
from app.domains.auth_core.types import AuthContext
from app.domains.identity.dependencies import get_current_user
from app.domains.identity.repository import UserRepository
from app.domains.identity.schemas import TokenResponse, UserLoginRequest, UserRead, UserRegisterRequest
from app.domains.identity.service import AuthService

router = APIRouter()


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(payload: UserRegisterRequest, db: AsyncSession = Depends(get_db)):
    return await AuthService(UserRepository(db)).register(payload)


@router.post("/login", response_model=TokenResponse)
async def login(payload: UserLoginRequest, request: Request, db: AsyncSession = Depends(get_db)):
    # Delegates to the same auth_core login flow as POST /auth/login (lockout +
    # audit + session/token issuance) so this legacy path can't be used to
    # bypass account-lockout protection. See ADR-002 durum güncellemesi (2026-07-18).
    context = AuthContext(
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        correlation_id=request.headers.get("x-correlation-id"),
    )

    try:
        pair = await authenticate_and_issue_tokens(
            identifier=payload.email,
            password=payload.password,
            context=context,
            user_repository=UserRepository(db),
            auth_service=build_auth_service(db),
        )
    except AuthenticationCoreError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.code) from exc

    return TokenResponse(access_token=pair.access_token)


@router.get("/me", response_model=UserRead)
async def me(current_user=Depends(get_current_user)):
    return current_user
