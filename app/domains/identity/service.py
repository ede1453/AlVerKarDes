from fastapi import HTTPException, status

from app.core.security import create_access_token, hash_password, verify_password
from app.domains.identity.repository import UserRepository
from app.domains.identity.schemas import TokenResponse, UserLoginRequest, UserRegisterRequest


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

    async def login(self, payload: UserLoginRequest) -> TokenResponse:
        user = await self.repo.get_by_email(payload.email)
        if not user or not user.password_hash or not verify_password(payload.password, user.password_hash):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail={"code": "INVALID_CREDENTIALS"})
        return TokenResponse(access_token=create_access_token(str(user.id)))
