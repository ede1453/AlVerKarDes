from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
from typing import Any
from uuid import uuid4


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class DealPersistenceService:
    def __init__(self) -> None:
        self._records: dict[str, dict[str, Any]] = {}
        self._snapshots: dict[str, dict[str, Any]] = {}
        self._checkpoints: dict[str, dict[str, Any]] = {}
        self._archives: dict[str, dict[str, Any]] = {}
        self._recovery_events: list[dict[str, Any]] = []

    # RC160 — Persistent record foundation
    def persist_deal(
        self,
        *,
        deal_id: str,
        payload: dict[str, Any],
        expected_version: int | None = None,
    ) -> dict[str, Any]:
        existing = self._records.get(deal_id)

        if existing is None:
            version = 1
        else:
            current_version = int(existing["version"])

            if (
                expected_version is not None
                and expected_version != current_version
            ):
                return {
                    "persisted": False,
                    "reason": "VERSION_CONFLICT",
                    "current_version": current_version,
                    "record": deepcopy(existing),
                }

            version = current_version + 1

        record = {
            "deal_id": deal_id,
            "version": version,
            "payload": deepcopy(payload),
            "payload_hash": self._hash_payload(payload),
            "persisted_at": now_iso(),
            "archived": False,
        }

        self._records[deal_id] = record

        return {
            "persisted": True,
            "reason": "DEAL_PERSISTED",
            "record": deepcopy(record),
            "metadata": {
                "persistence_version": "deal_persistence_v1"
            },
        }

    def get_record(
        self,
        deal_id: str,
    ) -> dict[str, Any] | None:
        record = self._records.get(deal_id)
        return deepcopy(record) if record else None

    # RC161 — Snapshot export
    def create_snapshot(
        self,
        *,
        deal_id: str,
        include_metadata: bool = True,
    ) -> dict[str, Any]:
        record = self._records.get(deal_id)

        if record is None:
            return {
                "created": False,
                "reason": "DEAL_NOT_FOUND",
                "snapshot": None,
            }

        snapshot_id = str(uuid4())
        snapshot_payload = {
            "deal_id": deal_id,
            "record_version": record["version"],
            "payload": deepcopy(record["payload"]),
        }

        if include_metadata:
            snapshot_payload["persistence"] = {
                "payload_hash": record["payload_hash"],
                "persisted_at": record["persisted_at"],
            }

        snapshot = {
            "snapshot_id": snapshot_id,
            "deal_id": deal_id,
            "record_version": record["version"],
            "snapshot_payload": snapshot_payload,
            "snapshot_hash": self._hash_payload(
                snapshot_payload
            ),
            "created_at": now_iso(),
        }

        self._snapshots[snapshot_id] = snapshot

        return {
            "created": True,
            "reason": "SNAPSHOT_CREATED",
            "snapshot": deepcopy(snapshot),
            "metadata": {
                "snapshot_version": "deal_snapshot_v1"
            },
        }

    def get_snapshot(
        self,
        snapshot_id: str,
    ) -> dict[str, Any] | None:
        snapshot = self._snapshots.get(snapshot_id)
        return deepcopy(snapshot) if snapshot else None

    # RC162 — Lifecycle checkpoint
    def create_checkpoint(
        self,
        *,
        deal_id: str,
        lifecycle_status: str,
        decision_version: int | None = None,
        event_cursor: int = 0,
    ) -> dict[str, Any]:
        record = self._records.get(deal_id)

        if record is None:
            return {
                "created": False,
                "reason": "DEAL_NOT_FOUND",
                "checkpoint": None,
            }

        checkpoint_id = str(uuid4())
        checkpoint = {
            "checkpoint_id": checkpoint_id,
            "deal_id": deal_id,
            "record_version": record["version"],
            "lifecycle_status": lifecycle_status,
            "decision_version": decision_version,
            "event_cursor": max(int(event_cursor), 0),
            "created_at": now_iso(),
        }

        self._checkpoints[checkpoint_id] = checkpoint

        return {
            "created": True,
            "reason": "CHECKPOINT_CREATED",
            "checkpoint": deepcopy(checkpoint),
            "metadata": {
                "checkpoint_version": "deal_checkpoint_v1"
            },
        }

    def latest_checkpoint(
        self,
        deal_id: str,
    ) -> dict[str, Any] | None:
        checkpoints = [
            item
            for item in self._checkpoints.values()
            if item["deal_id"] == deal_id
        ]

        if not checkpoints:
            return None

        checkpoints.sort(
            key=lambda item: item["created_at"]
        )
        return deepcopy(checkpoints[-1])

    # RC163 — Archive and retention
    def archive_deal(
        self,
        *,
        deal_id: str,
        reason: str,
        actor: str = "system",
    ) -> dict[str, Any]:
        record = self._records.get(deal_id)

        if record is None:
            return {
                "archived": False,
                "reason": "DEAL_NOT_FOUND",
                "archive": None,
            }

        if record["archived"]:
            archive = self._archives.get(deal_id)
            return {
                "archived": False,
                "reason": "DEAL_ALREADY_ARCHIVED",
                "archive": deepcopy(archive),
            }

        snapshot_result = self.create_snapshot(
            deal_id=deal_id
        )

        archive = {
            "archive_id": str(uuid4()),
            "deal_id": deal_id,
            "record_version": record["version"],
            "snapshot_id": snapshot_result[
                "snapshot"
            ]["snapshot_id"],
            "reason": reason,
            "actor": actor,
            "archived_at": now_iso(),
        }

        record["archived"] = True
        self._archives[deal_id] = archive

        return {
            "archived": True,
            "reason": "DEAL_ARCHIVED",
            "archive": deepcopy(archive),
            "metadata": {
                "archive_version": "deal_archive_v1"
            },
        }

    def list_archives(self) -> dict[str, Any]:
        archives = deepcopy(
            list(self._archives.values())
        )

        return {
            "archive_count": len(archives),
            "archives": archives,
        }

    # RC164 — Recovery and integrity validation
    def recover_from_snapshot(
        self,
        *,
        snapshot_id: str,
        expected_snapshot_hash: str | None = None,
    ) -> dict[str, Any]:
        snapshot = self._snapshots.get(snapshot_id)

        if snapshot is None:
            return {
                "recovered": False,
                "reason": "SNAPSHOT_NOT_FOUND",
                "record": None,
            }

        if (
            expected_snapshot_hash is not None
            and expected_snapshot_hash
            != snapshot["snapshot_hash"]
        ):
            return {
                "recovered": False,
                "reason": "SNAPSHOT_HASH_MISMATCH",
                "record": None,
            }

        recalculated_hash = self._hash_payload(
            snapshot["snapshot_payload"]
        )

        if recalculated_hash != snapshot[
            "snapshot_hash"
        ]:
            return {
                "recovered": False,
                "reason": "SNAPSHOT_INTEGRITY_FAILED",
                "record": None,
            }

        deal_id = snapshot["deal_id"]
        payload = deepcopy(
            snapshot["snapshot_payload"]["payload"]
        )

        existing = self._records.get(deal_id)
        next_version = (
            int(existing["version"]) + 1
            if existing
            else snapshot["record_version"] + 1
        )

        record = {
            "deal_id": deal_id,
            "version": next_version,
            "payload": payload,
            "payload_hash": self._hash_payload(payload),
            "persisted_at": now_iso(),
            "archived": False,
        }

        self._records[deal_id] = record

        event = {
            "recovery_event_id": str(uuid4()),
            "deal_id": deal_id,
            "snapshot_id": snapshot_id,
            "restored_version": next_version,
            "created_at": now_iso(),
        }

        self._recovery_events.append(event)

        return {
            "recovered": True,
            "reason": "SNAPSHOT_RECOVERED",
            "record": deepcopy(record),
            "event": deepcopy(event),
            "metadata": {
                "recovery_version": "deal_recovery_v1"
            },
        }

    def list_recovery_events(
        self,
        *,
        deal_id: str | None = None,
    ) -> dict[str, Any]:
        events = list(self._recovery_events)

        if deal_id is not None:
            events = [
                item
                for item in events
                if item["deal_id"] == deal_id
            ]

        return {
            "event_count": len(events),
            "events": deepcopy(events),
        }

    def _hash_payload(
        self,
        payload: dict[str, Any],
    ) -> str:
        import json

        serialized = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )

        return sha256(
            serialized.encode("utf-8")
        ).hexdigest()
