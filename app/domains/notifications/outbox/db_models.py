import uuid
from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class NotificationOutboxItemModel(Base):
    __tablename__ = "notification_outbox_items"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    user_id: Mapped[str] = mapped_column(String, nullable=False)
    channel: Mapped[str] = mapped_column(String, nullable=False, default="in_app")
    title: Mapped[str] = mapped_column(String, nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    # Plain VARCHAR, not a native Postgres enum -- project-wide convention
    # (ADR-005), same as jobs.status/provider_schedules.status.
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="PENDING")
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_retries: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    next_retry_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    provider: Mapped[str] = mapped_column(String, nullable=False, default="mock")
    idempotency_key: Mapped[str | None] = mapped_column(String, nullable=True)
    snoozed_until: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    # SCALE-007: claim ownership -- same locked_by/locked_at discipline as
    # jobs (SCALE-003)/provider_schedules (SCALE-004). Set atomically by
    # claim_next() (SELECT FOR UPDATE SKIP LOCKED), cleared on
    # delivered/failed/dead-letter. A PROCESSING item whose locked_at is
    # older than the stale-lock window is treated as an abandoned claim
    # (worker crashed mid-delivery) and becomes claimable again. This is a
    # NEW mechanism -- the pre-SCALE-007 code had no claim tracking at all
    # (claim_next() did an unguarded list_pending()+mark_processing(),
    # which was never safe even single-process under concurrency).
    locked_by: Mapped[str | None] = mapped_column(String, nullable=True)
    locked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
