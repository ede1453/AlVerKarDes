from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.identity.models import User


class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_email(self, email: str) -> User | None:
        result = await self.db.execute(select(User).where(User.email == email.lower(), User.deleted_at.is_(None)))
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: str) -> User | None:
        result = await self.db.execute(select(User).where(User.id == user_id, User.deleted_at.is_(None)))
        return result.scalar_one_or_none()

    async def create_user(self, *, email: str, password_hash: str, display_name: str | None) -> User:
        user = User(email=email.lower(), password_hash=password_hash, display_name=display_name)
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def set_password_hash(self, user_id, password_hash: str) -> None:
        # CLIENT-002f: the write side of complete_password_reset()'s
        # set_user_password_hash callback.
        result = await self.db.execute(select(User).where(User.id == user_id, User.deleted_at.is_(None)))
        user = result.scalar_one_or_none()
        if user is None:
            return
        user.password_hash = password_hash
        await self.db.commit()
