from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class DealStorageBase(DeclarativeBase):
    pass


class DealStorageRecord(DealStorageBase):
    __tablename__ = "deal_storage_records"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
    )
    deal_id: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
        unique=True,
        index=True,
    )
    version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    payload: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
    )
    payload_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )
    archived: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    persisted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )


class DealStorageOutboxEvent(DealStorageBase):
    __tablename__ = "deal_storage_outbox_events"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
    )
    aggregate_type: Mapped[str] = mapped_column(
        String(80),
        nullable=False,
    )
    aggregate_id: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
        index=True,
    )
    event_type: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
    )
    payload: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="PENDING",
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )


class DealStorageIntegrityReport(DealStorageBase):
    __tablename__ = "deal_storage_integrity_reports"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
    )
    healthy: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
    )
    record_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    issue_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    issues: Mapped[list] = mapped_column(
        JSON,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )


class DealStorageBackupManifest(DealStorageBase):
    __tablename__ = "deal_storage_backup_manifests"
    __table_args__ = (
        UniqueConstraint(
            "backup_name",
            "manifest_hash",
            name="uq_deal_storage_backup_manifest",
        ),
    )

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
    )
    backup_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    record_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    manifest_payload: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
    )
    manifest_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
