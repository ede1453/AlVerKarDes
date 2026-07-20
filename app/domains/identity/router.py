from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.domains.auth_core.dependencies import build_auth_service
from app.domains.auth_core.login_flow import authenticate_and_issue_tokens
from app.domains.auth_core.service import AuthenticationCoreError
from app.domains.auth_core.types import AuthContext
from app.domains.identity.dependencies import ensure_owner, get_current_user
from app.domains.identity.repository import UserRepository
from app.domains.identity.schemas import (
    TokenResponse,
    UserLoginRequest,
    UserProfileUpdateRequest,
    UserRead,
    UserRegisterRequest,
)
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


@router.patch("/me", response_model=UserRead)
async def update_profile(
    payload: UserProfileUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    # CLIENT-002h: user_id in the body + ensure_owner(), same OWNER_ONLY
    # shape as every other CLIENT-002 settings endpoint (watchlist,
    # deal-notifications preferences) -- redundant with "always operates
    # on the token holder" in principle, but consistent with this
    # codebase's established convention and gives a real cross-user
    # attack vector to test (impersonation via a mismatched user_id).
    ensure_owner(current_user, str(payload.user_id))
    updated = await UserRepository(db).update_profile(
        user_id=payload.user_id,
        display_name=payload.display_name,
        preferred_language=payload.preferred_language,
        preferred_country=payload.preferred_country,
    )
    if updated is None:
        raise HTTPException(status_code=404, detail="USER_NOT_FOUND")
    return updated
