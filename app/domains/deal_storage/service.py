from __future__ import annotations

import json
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from typing import Any
from uuid import uuid4


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def now_iso() -> str:
    return now_utc().isoformat()


class DealStorageRepository:
    def __init__(self) -> None:
        self._records: dict[str, dict[str, Any]] = {}
        self._outbox: list[dict[str, Any]] = []
        self._purge_log: list[dict[str, Any]] = []
        self._integrity_reports: list[dict[str, Any]] = []
        self._backup_manifests: dict[str, dict[str, Any]] = {}

    # RC165 — Repository contract
    def upsert(
        self,
        *,
        deal_id: str,
        payload: dict[str, Any],
        version: int,
        archived: bool = False,
        persisted_at: str | None = None,
    ) -> dict[str, Any]:
        record = {
            "deal_id": deal_id,
            "payload": deepcopy(payload),
            "payload_hash": self._hash(payload),
            "version": int(version),
            "archived": bool(archived),
            "persisted_at": persisted_at or now_iso(),
        }
        self._records[deal_id] = record
        return deepcopy(record)

    def get(self, deal_id: str) -> dict[str, Any] | None:
        record = self._records.get(deal_id)
        return deepcopy(record) if record else None

    def list_records(
        self,
        *,
        archived: bool | None = None,
    ) -> list[dict[str, Any]]:
        records = list(self._records.values())
        if archived is not None:
            records = [
                item for item in records
                if item["archived"] is archived
            ]
        return deepcopy(records)

    # RC166 — Transaction boundary + outbox
    def save_with_outbox(
        self,
        *,
        deal_id: str,
        payload: dict[str, Any],
        version: int,
        event_type: str,
        event_payload: dict[str, Any],
    ) -> dict[str, Any]:
        previous = deepcopy(self._records.get(deal_id))

        try:
            record = self.upsert(
                deal_id=deal_id,
                payload=payload,
                version=version,
            )

            event = {
                "outbox_event_id": str(uuid4()),
                "aggregate_type": "deal",
                "aggregate_id": deal_id,
                "event_type": event_type,
                "payload": deepcopy(event_payload),
                "status": "PENDING",
                "created_at": now_iso(),
                "published_at": None,
            }
            self._outbox.append(event)

            return {
                "committed": True,
                "record": record,
                "event": deepcopy(event),
            }
        except Exception:
            if previous is None:
                self._records.pop(deal_id, None)
            else:
                self._records[deal_id] = previous
            raise

    def list_outbox(
        self,
        *,
        status: str | None = None,
    ) -> list[dict[str, Any]]:
        events = list(self._outbox)
        if status is not None:
            events = [
                item for item in events
                if item["status"] == status
            ]
        return deepcopy(events)

    def mark_outbox_published(
        self,
        outbox_event_id: str,
    ) -> dict[str, Any] | None:
        for event in self._outbox:
            if event["outbox_event_id"] == outbox_event_id:
                event["status"] = "PUBLISHED"
                event["published_at"] = now_iso()
                return deepcopy(event)
        return None

    # RC167 — Retention purge
    def purge_archived(
        self,
        *,
        older_than_days: int,
        reference_time: str | None = None,
        dry_run: bool = True,
    ) -> dict[str, Any]:
        reference = (
            datetime.fromisoformat(reference_time)
            if reference_time
            else now_utc()
        )
        cutoff = reference - timedelta(days=max(older_than_days, 0))

        candidates = [
            item
            for item in self._records.values()
            if item["archived"]
            and datetime.fromisoformat(item["persisted_at"]) < cutoff
        ]

        purged_ids = [item["deal_id"] for item in candidates]

        if not dry_run:
            for deal_id in purged_ids:
                self._records.pop(deal_id, None)

        log = {
            "purge_id": str(uuid4()),
            "dry_run": dry_run,
            "older_than_days": older_than_days,
            "candidate_count": len(candidates),
            "purged_count": 0 if dry_run else len(candidates),
            "deal_ids": purged_ids,
            "created_at": now_iso(),
        }
        self._purge_log.append(log)

        return {
            "completed": True,
            "dry_run": dry_run,
            "candidate_count": len(candidates),
            "purged_count": 0 if dry_run else len(candidates),
            "deal_ids": purged_ids,
            "metadata": {
                "retention_version": "deal_retention_v1"
            },
        }

    # RC168 — Integrity audit
    def audit_integrity(self) -> dict[str, Any]:
        issues = []

        for record in self._records.values():
            calculated = self._hash(record["payload"])
            if calculated != record["payload_hash"]:
                issues.append({
                    "deal_id": record["deal_id"],
                    "issue": "PAYLOAD_HASH_MISMATCH",
                    "expected": record["payload_hash"],
                    "actual": calculated,
                })

            if int(record["version"]) <= 0:
                issues.append({
                    "deal_id": record["deal_id"],
                    "issue": "INVALID_VERSION",
                })

        report = {
            "report_id": str(uuid4()),
            "record_count": len(self._records),
            "issue_count": len(issues),
            "healthy": len(issues) == 0,
            "issues": issues,
            "created_at": now_iso(),
        }
        self._integrity_reports.append(report)

        return deepcopy(report)

    # RC169 — Backup manifest
    def create_backup_manifest(
        self,
        *,
        backup_name: str,
    ) -> dict[str, Any]:
        records = sorted(
            self._records.values(),
            key=lambda item: item["deal_id"],
        )

        manifest_payload = {
            "backup_name": backup_name,
            "record_count": len(records),
            "records": [
                {
                    "deal_id": item["deal_id"],
                    "version": item["version"],
                    "payload_hash": item["payload_hash"],
                    "archived": item["archived"],
                }
                for item in records
            ],
        }

        manifest_id = str(uuid4())
        manifest = {
            "manifest_id": manifest_id,
            **manifest_payload,
            "manifest_hash": self._hash(manifest_payload),
            "created_at": now_iso(),
        }
        self._backup_manifests[manifest_id] = manifest

        return deepcopy(manifest)

    def verify_backup_manifest(
        self,
        manifest_id: str,
    ) -> dict[str, Any]:
        manifest = self._backup_manifests.get(manifest_id)

        if manifest is None:
            return {
                "verified": False,
                "reason": "MANIFEST_NOT_FOUND",
            }

        payload = {
            "backup_name": manifest["backup_name"],
            "record_count": manifest["record_count"],
            "records": manifest["records"],
        }

        actual = self._hash(payload)

        return {
            "verified": actual == manifest["manifest_hash"],
            "reason": (
                "MANIFEST_VALID"
                if actual == manifest["manifest_hash"]
                else "MANIFEST_HASH_MISMATCH"
            ),
            "manifest_id": manifest_id,
        }

    def _hash(self, payload: dict[str, Any]) -> str:
        serialized = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )
        return sha256(serialized.encode("utf-8")).hexdigest()


class DealStorageOperationsService:
    def __init__(self) -> None:
        self.repository = DealStorageRepository()
