from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.domains.deal_storage.sqlalchemy_models import (
    DealStorageBackupManifest,
    DealStorageIntegrityReport,
    DealStorageOutboxEvent,
    DealStorageRecord,
)


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


class SQLAlchemyDealStorageRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    # RC170 — SQLAlchemy repository
    def upsert_record(
        self,
        *,
        deal_id: str,
        payload: dict[str, Any],
        expected_version: int | None = None,
        archived: bool = False,
    ) -> dict[str, Any]:
        record = self.session.scalar(
            select(DealStorageRecord).where(
                DealStorageRecord.deal_id == deal_id
            )
        )

        if record is None:
            version = 1
            record = DealStorageRecord(
                deal_id=deal_id,
                version=version,
                payload=payload,
                payload_hash=self._hash(payload),
                archived=archived,
                persisted_at=now_utc(),
            )
            self.session.add(record)
        else:
            if (
                expected_version is not None
                and expected_version != record.version
            ):
                return {
                    "persisted": False,
                    "reason": "VERSION_CONFLICT",
                    "current_version": record.version,
                }

            record.version += 1
            record.payload = payload
            record.payload_hash = self._hash(payload)
            record.archived = archived
            record.persisted_at = now_utc()

        self.session.flush()

        return {
            "persisted": True,
            "reason": "DEAL_RECORD_PERSISTED",
            "record": self._record_dict(record),
        }

    def get_record(
        self,
        deal_id: str,
    ) -> dict[str, Any] | None:
        record = self.session.scalar(
            select(DealStorageRecord).where(
                DealStorageRecord.deal_id == deal_id
            )
        )
        return (
            self._record_dict(record)
            if record is not None
            else None
        )

    # RC172 — Atomic record + outbox transaction
    def save_with_outbox(
        self,
        *,
        deal_id: str,
        payload: dict[str, Any],
        expected_version: int | None,
        event_type: str,
        event_payload: dict[str, Any],
    ) -> dict[str, Any]:
        try:
            result = self.upsert_record(
                deal_id=deal_id,
                payload=payload,
                expected_version=expected_version,
            )

            if not result["persisted"]:
                self.session.rollback()
                return {
                    "committed": False,
                    **result,
                }

            event = DealStorageOutboxEvent(
                aggregate_type="deal",
                aggregate_id=deal_id,
                event_type=event_type,
                payload=event_payload,
                status="PENDING",
                created_at=now_utc(),
                published_at=None,
            )
            self.session.add(event)
            self.session.commit()

            return {
                "committed": True,
                "record": result["record"],
                "event": self._event_dict(event),
            }
        except Exception:
            self.session.rollback()
            raise

    def claim_pending_events(
        self,
        *,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        events = list(
            self.session.scalars(
                select(DealStorageOutboxEvent)
                .where(
                    DealStorageOutboxEvent.status
                    == "PENDING"
                )
                .order_by(
                    DealStorageOutboxEvent.created_at
                )
                .limit(max(1, limit))
            )
        )

        for event in events:
            event.status = "PROCESSING"

        self.session.commit()

        return [
            self._event_dict(event)
            for event in events
        ]

    def mark_event_published(
        self,
        event_id: str,
    ) -> dict[str, Any] | None:
        event = self.session.get(
            DealStorageOutboxEvent,
            event_id,
        )

        if event is None:
            return None

        event.status = "PUBLISHED"
        event.published_at = now_utc()
        self.session.commit()

        return self._event_dict(event)

    # RC173 — Database retention
    def purge_archived(
        self,
        *,
        older_than_days: int,
        reference_time: datetime | None = None,
        dry_run: bool = True,
    ) -> dict[str, Any]:
        reference = reference_time or now_utc()
        cutoff = reference - timedelta(
            days=max(older_than_days, 0)
        )

        candidate_ids = list(
            self.session.scalars(
                select(DealStorageRecord.deal_id)
                .where(
                    DealStorageRecord.archived.is_(True),
                    DealStorageRecord.persisted_at < cutoff,
                )
            )
        )

        if not dry_run and candidate_ids:
            self.session.execute(
                delete(DealStorageRecord).where(
                    DealStorageRecord.deal_id.in_(
                        candidate_ids
                    )
                )
            )
            self.session.commit()

        return {
            "completed": True,
            "dry_run": dry_run,
            "candidate_count": len(candidate_ids),
            "purged_count": (
                0
                if dry_run
                else len(candidate_ids)
            ),
            "deal_ids": candidate_ids,
        }

    # RC174 — Database integrity audit
    def audit_integrity(self) -> dict[str, Any]:
        records = list(
            self.session.scalars(
                select(DealStorageRecord)
            )
        )

        issues: list[dict[str, Any]] = []

        for record in records:
            actual_hash = self._hash(record.payload)

            if actual_hash != record.payload_hash:
                issues.append(
                    {
                        "deal_id": record.deal_id,
                        "issue": "PAYLOAD_HASH_MISMATCH",
                    }
                )

            if record.version <= 0:
                issues.append(
                    {
                        "deal_id": record.deal_id,
                        "issue": "INVALID_VERSION",
                    }
                )

        report = DealStorageIntegrityReport(
            healthy=len(issues) == 0,
            record_count=len(records),
            issue_count=len(issues),
            issues=issues,
            created_at=now_utc(),
        )
        self.session.add(report)
        self.session.commit()

        return {
            "report_id": report.id,
            "healthy": report.healthy,
            "record_count": report.record_count,
            "issue_count": report.issue_count,
            "issues": report.issues,
        }

    # RC175 — Database backup manifest
    def create_backup_manifest(
        self,
        *,
        backup_name: str,
    ) -> dict[str, Any]:
        records = list(
            self.session.scalars(
                select(DealStorageRecord).order_by(
                    DealStorageRecord.deal_id
                )
            )
        )

        payload = {
            "backup_name": backup_name,
            "record_count": len(records),
            "records": [
                {
                    "deal_id": record.deal_id,
                    "version": record.version,
                    "payload_hash": record.payload_hash,
                    "archived": record.archived,
                }
                for record in records
            ],
        }

        manifest_hash = self._hash(payload)

        manifest = DealStorageBackupManifest(
            backup_name=backup_name,
            record_count=len(records),
            manifest_payload=payload,
            manifest_hash=manifest_hash,
            created_at=now_utc(),
        )
        self.session.add(manifest)
        self.session.commit()

        return {
            "manifest_id": manifest.id,
            "backup_name": manifest.backup_name,
            "record_count": manifest.record_count,
            "manifest_hash": manifest.manifest_hash,
            "created_at": manifest.created_at.isoformat(),
        }

    def verify_backup_manifest(
        self,
        manifest_id: str,
    ) -> dict[str, Any]:
        manifest = self.session.get(
            DealStorageBackupManifest,
            manifest_id,
        )

        if manifest is None:
            return {
                "verified": False,
                "reason": "MANIFEST_NOT_FOUND",
            }

        actual = self._hash(
            manifest.manifest_payload
        )

        return {
            "verified": actual == manifest.manifest_hash,
            "reason": (
                "MANIFEST_VALID"
                if actual == manifest.manifest_hash
                else "MANIFEST_HASH_MISMATCH"
            ),
            "manifest_id": manifest_id,
        }

    def _hash(
        self,
        payload: dict[str, Any],
    ) -> str:
        serialized = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )
        return sha256(
            serialized.encode("utf-8")
        ).hexdigest()

    def _record_dict(
        self,
        record: DealStorageRecord,
    ) -> dict[str, Any]:
        return {
            "id": record.id,
            "deal_id": record.deal_id,
            "version": record.version,
            "payload": record.payload,
            "payload_hash": record.payload_hash,
            "archived": record.archived,
            "persisted_at": record.persisted_at.isoformat(),
        }

    def _event_dict(
        self,
        event: DealStorageOutboxEvent,
    ) -> dict[str, Any]:
        return {
            "id": event.id,
            "aggregate_type": event.aggregate_type,
            "aggregate_id": event.aggregate_id,
            "event_type": event.event_type,
            "payload": event.payload,
            "status": event.status,
            "created_at": event.created_at.isoformat(),
            "published_at": (
                event.published_at.isoformat()
                if event.published_at
                else None
            ),
        }
