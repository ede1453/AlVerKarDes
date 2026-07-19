import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class NotificationPreferenceModel(Base):
    __tablename__ = "notification_preferences"

    # CLIENT-002g: one row per user -- user_id is the primary key (not a
    # separate id + unique index), matches the 1:1 relationship the
    # existing in-memory NotificationPreferenceService already assumed
    # (self._preferences[user_id] = ...).
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    enabled_channels: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    minimum_confidence: Mapped[float] = mapped_column(Float, nullable=False, default=70.0)
    minimum_discount_pct: Mapped[float] = mapped_column(Float, nullable=False, default=10.0)
    quiet_hours_enabled: Mapped[bool] = mapped_column(default=False, nullable=False)
    # Plain HH:MM strings -- matches the existing API contract exactly
    # (PreferenceRequest.quiet_hours_start/end are str already, parsed with
    # time.fromisoformat() at read time by QuietHoursService); not worth
    # introducing a sa.Time column and a conversion layer for this.
    quiet_hours_start: Mapped[str] = mapped_column(String(5), nullable=False, default="22:00")
    quiet_hours_end: Mapped[str] = mapped_column(String(5), nullable=False, default="08:00")
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
