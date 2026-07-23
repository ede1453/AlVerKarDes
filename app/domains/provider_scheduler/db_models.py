import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ProviderScheduleModel(Base):
    __tablename__ = "provider_schedules"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    providers: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    interval_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=60)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    # Plain VARCHAR, not a native Postgres enum -- project-wide convention
    # (ADR-005), same as jobs.status. ACTIVE/DISABLED are steady states;
    # RUNNING is the transient claimed-and-locked state (SCALE-004).
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="ACTIVE")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_result: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    # SCALE-004: claim ownership -- same locked_by/locked_at discipline as
    # jobs (SCALE-003). Set atomically by claim() (SELECT FOR UPDATE SKIP
    # LOCKED), cleared by complete_run(). A RUNNING schedule whose locked_at
    # is older than the stale-lock window is treated as an abandoned claim
    # (worker crashed mid-check) and becomes claimable again.
    locked_by: Mapped[str | None] = mapped_column(String, nullable=True)
    locked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
