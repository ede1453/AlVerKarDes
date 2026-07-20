import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class SubscriptionTier(str, enum.Enum):
    FREE = "FREE"
    PREMIUM = "PREMIUM"


class SubscriptionModel(Base):
    __tablename__ = "subscriptions"

    # BILL-001: one row per user, current-state only (not a billing-history
    # ledger) -- same 1:1 user_id-as-PK pattern as NotificationPreferenceModel
    # (CLIENT-002g), not a separate id + unique index. A full history table
    # was considered in ADR-016 but deferred until actually needed.
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    # native_enum=False -- project-wide convention (ADR-005): plain VARCHAR
    # column, no CREATE TYPE round-trip on migrations.
    tier: Mapped[SubscriptionTier] = mapped_column(
        Enum(SubscriptionTier, native_enum=False, length=20),
        default=SubscriptionTier.FREE,
        nullable=False,
    )
    provider_reference: Mapped[str | None] = mapped_column(String(200), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
