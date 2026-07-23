from datetime import datetime

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class UserProfileModel(Base):
    __tablename__ = "user_profiles"

    # Plain String PK, not a UUID FK to users.id -- mirrors
    # notification_outbox_items.user_id (SCALE-007 Part 1). Real production
    # traffic always uses a real user UUID (ensure_owner() enforces this at
    # the API layer), but several existing unit tests call
    # UserProfileService/ShoppingPipelineService directly with arbitrary
    # string ids ("user-1") -- a UUID FK would reject those with no
    # corresponding row in `users`, and casting would raise on non-UUID
    # strings. Keeping it a plain string avoids that entirely.
    user_id: Mapped[str] = mapped_column(String, primary_key=True)
    preferred_product_keys: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    avoided_product_keys: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    preferred_marketplaces: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    blocked_marketplaces: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    preferred_brands: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    risk_tolerance: Mapped[str] = mapped_column(String, nullable=False, default="MEDIUM")
    profile_score: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    metadata_json: Mapped[dict] = mapped_column("metadata", JSONB, nullable=False, default=dict)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
