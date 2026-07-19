import enum

from sqlalchemy import Enum, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class UserStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    DISABLED = "DISABLED"
    PENDING_VERIFICATION = "PENDING_VERIFICATION"
    DELETED = "DELETED"


class UserRole(str, enum.Enum):
    SHOPPER = "SHOPPER"
    OPERATOR = "OPERATOR"
    RELEASE_MANAGER = "RELEASE_MANAGER"
    SUPERADMIN = "SUPERADMIN"


class User(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False, index=True)
    username: Mapped[str | None] = mapped_column(String(80), unique=True)
    display_name: Mapped[str | None] = mapped_column(String(160))
    password_hash: Mapped[str | None] = mapped_column(Text)
    # native_enum=False: migration 0001_initial_stabilized created this column as a
    # plain VARCHAR(50), not a Postgres enum type. Without this, SQLAlchemy binds
    # values as ::userstatus (a native PG enum type that was never created),
    # raising asyncpg.exceptions.UndefinedObjectError on every INSERT/UPDATE.
    status: Mapped[UserStatus] = mapped_column(
        Enum(UserStatus, native_enum=False, length=50), default=UserStatus.ACTIVE, nullable=False
    )
    # native_enum=False for the same reason as `status` above (see ADR-005) --
    # migration 0016_user_roles creates this as a plain VARCHAR(20).
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, native_enum=False, length=20), default=UserRole.SHOPPER, nullable=False
    )
    preferred_language: Mapped[str] = mapped_column(String(10), default="en", nullable=False)
    preferred_currency: Mapped[str] = mapped_column(String(3), default="EUR", nullable=False)
    preferred_country: Mapped[str] = mapped_column(String(2), default="DE", nullable=False)
