import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class JobModel(Base):
    __tablename__ = "jobs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    job_type: Mapped[str] = mapped_column(String, nullable=False)
    # Plain VARCHAR, not a native Postgres enum -- project-wide convention
    # (ADR-005), same as watchlist_items.status.
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="PENDING")
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    result: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    # SCALE-003: claim ownership -- set atomically by claim_next() (SELECT
    # FOR UPDATE SKIP LOCKED), cleared on completion/failure. locked_at also
    # doubles as the stale-lock cutoff: a RUNNING job whose locked_at is
    # older than the stale-lock window is treated as abandoned (worker
    # crashed without releasing) and becomes claimable again.
    locked_by: Mapped[str | None] = mapped_column(String, nullable=True)
    locked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
