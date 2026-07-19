from fastapi import HTTPException, status

from app.core.security import hash_password
from app.domains.identity.repository import UserRepository
from app.domains.identity.schemas import UserRegisterRequest


class AuthService:
    def __init__(self, repo: UserRepository):
        self.repo = repo

    async def register(self, payload: UserRegisterRequest):
        if await self.repo.get_by_email(payload.email):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail={"code": "EMAIL_ALREADY_REGISTERED"})
        return await self.repo.create_user(
            email=payload.email,
            password_hash=hash_password(payload.password),
            display_name=payload.display_name,
        )

    # login() was removed 2026-07-18: it verified passwords itself and issued a
    # bare JWT with no lockout/audit trail, running in parallel with (and
    # bypassable around) auth_core's protections. Login now goes through
    # app.domains.auth_core.login_flow.authenticate_and_issue_tokens for both
    # /identity/login and /auth/login. See ADR-002 durum güncellemesi.
