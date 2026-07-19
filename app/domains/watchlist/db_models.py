import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class WatchlistItemStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


class WatchlistItemModel(Base):
    __tablename__ = "watchlist_items"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    product_key: Mapped[str] = mapped_column(String, nullable=False)
    query: Mapped[str] = mapped_column(String, nullable=False)
    target_price: Mapped[str | None] = mapped_column(String, nullable=True)
    marketplaces: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    channels: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    # native_enum=False -- this project avoids native Postgres enum types
    # project-wide (see identity.models.UserRole/UserStatus, ADR-005) so a
    # plain VARCHAR column can always be altered/read without a CREATE TYPE
    # round-trip. Applied here even though this is a brand-new table (no
    # legacy VARCHAR to match), for consistency with that standing rule.
    status: Mapped[WatchlistItemStatus] = mapped_column(
        Enum(WatchlistItemStatus, native_enum=False, length=20),
        default=WatchlistItemStatus.ACTIVE,
        nullable=False,
    )
    last_evaluation: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    metadata_json: Mapped[dict] = mapped_column("metadata", JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
