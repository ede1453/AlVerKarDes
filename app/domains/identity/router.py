from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.domains.identity.dependencies import get_current_user
from app.domains.identity.repository import UserRepository
from app.domains.identity.schemas import TokenResponse, UserLoginRequest, UserRead, UserRegisterRequest
from app.domains.identity.service import AuthService

router = APIRouter()


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(payload: UserRegisterRequest, db: AsyncSession = Depends(get_db)):
    return await AuthService(UserRepository(db)).register(payload)


@router.post("/login", response_model=TokenResponse)
async def login(payload: UserLoginRequest, db: AsyncSession = Depends(get_db)):
    return await AuthService(UserRepository(db)).login(payload)


@router.get("/me", response_model=UserRead)
async def me(current_user=Depends(get_current_user)):
    return current_user
