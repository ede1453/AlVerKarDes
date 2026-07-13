from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def now_iso() -> str:
    return now_utc().isoformat()


class DealStorageResilienceService:
    def __init__(self) -> None:
        self._outbox_events: dict[str, dict[str, Any]] = {}
        self._dead_letters: dict[str, dict[str, Any]] = {}
        self._backup_exports: dict[str, dict[str, Any]] = {}
        self._restore_validations: list[dict[str, Any]] = []
        self._health_samples: list[dict[str, Any]] = []

    # RC176 — Outbox publisher
    def enqueue_outbox(
        self,
        *,
        aggregate_id: str,
        event_type: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        event_id = str(uuid4())
        event = {
            "event_id": event_id,
            "aggregate_id": aggregate_id,
            "event_type": event_type,
            "payload": deepcopy(payload),
            "status": "PENDING",
            "attempt_count": 0,
            "next_attempt_at": now_iso(),
            "last_error": None,
            "created_at": now_iso(),
            "published_at": None,
        }
        self._outbox_events[event_id] = event
        return {
            "enqueued": True,
            "event": deepcopy(event),
        }

    def claim_publish_batch(
        self,
        *,
        limit: int = 100,
        at_time: str | None = None,
    ) -> dict[str, Any]:
        reference = (
            datetime.fromisoformat(at_time)
            if at_time
            else now_utc()
        )

        candidates = [
            event
            for event in self._outbox_events.values()
            if event["status"] in {"PENDING", "RETRY"}
            and datetime.fromisoformat(
                event["next_attempt_at"]
            ) <= reference
        ]

        candidates.sort(
            key=lambda item: item["created_at"]
        )

        claimed = candidates[:max(1, limit)]

        for event in claimed:
            event["status"] = "PROCESSING"
            event["attempt_count"] += 1

        return {
            "claimed_count": len(claimed),
            "events": deepcopy(claimed),
        }

    def mark_published(
        self,
        event_id: str,
    ) -> dict[str, Any]:
        event = self._outbox_events.get(event_id)

        if event is None:
            return {
                "updated": False,
                "reason": "EVENT_NOT_FOUND",
            }

        event["status"] = "PUBLISHED"
        event["published_at"] = now_iso()
        event["last_error"] = None

        return {
            "updated": True,
            "event": deepcopy(event),
        }

    # RC177 — Retry and dead-letter
    def mark_publish_failed(
        self,
        *,
        event_id: str,
        error: str,
        max_attempts: int = 5,
        base_delay_seconds: int = 30,
    ) -> dict[str, Any]:
        event = self._outbox_events.get(event_id)

        if event is None:
            return {
                "updated": False,
                "reason": "EVENT_NOT_FOUND",
            }

        event["last_error"] = error

        if event["attempt_count"] >= max_attempts:
            event["status"] = "DEAD_LETTER"
            dead_letter_id = str(uuid4())
            dead_letter = {
                "dead_letter_id": dead_letter_id,
                "event_id": event_id,
                "aggregate_id": event["aggregate_id"],
                "event_type": event["event_type"],
                "payload": deepcopy(event["payload"]),
                "attempt_count": event["attempt_count"],
                "last_error": error,
                "created_at": now_iso(),
                "replayed": False,
                "replayed_at": None,
            }
            self._dead_letters[
                dead_letter_id
            ] = dead_letter

            return {
                "updated": True,
                "status": "DEAD_LETTER",
                "event": deepcopy(event),
                "dead_letter": deepcopy(dead_letter),
            }

        delay = base_delay_seconds * (
            2 ** max(event["attempt_count"] - 1, 0)
        )

        event["status"] = "RETRY"
        event["next_attempt_at"] = (
            now_utc()
            + timedelta(seconds=delay)
        ).isoformat()

        return {
            "updated": True,
            "status": "RETRY",
            "delay_seconds": delay,
            "event": deepcopy(event),
        }

    def replay_dead_letter(
        self,
        dead_letter_id: str,
    ) -> dict[str, Any]:
        item = self._dead_letters.get(
            dead_letter_id
        )

        if item is None:
            return {
                "replayed": False,
                "reason": "DEAD_LETTER_NOT_FOUND",
            }

        event = self._outbox_events[
            item["event_id"]
        ]
        event["status"] = "PENDING"
        event["attempt_count"] = 0
        event["next_attempt_at"] = now_iso()
        event["last_error"] = None

        item["replayed"] = True
        item["replayed_at"] = now_iso()

        return {
            "replayed": True,
            "event": deepcopy(event),
            "dead_letter": deepcopy(item),
        }

    # RC178 — Backup export
    def create_backup_export(
        self,
        *,
        backup_name: str,
        records: list[dict[str, Any]],
        manifests: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        export_id = str(uuid4())
        export = {
            "export_id": export_id,
            "backup_name": backup_name,
            "record_count": len(records),
            "manifest_count": len(
                manifests or []
            ),
            "records": deepcopy(records),
            "manifests": deepcopy(
                manifests or []
            ),
            "created_at": now_iso(),
        }
        self._backup_exports[
            export_id
        ] = export

        return {
            "created": True,
            "export": deepcopy(export),
        }

    def get_backup_export(
        self,
        export_id: str,
    ) -> dict[str, Any] | None:
        item = self._backup_exports.get(export_id)
        return deepcopy(item) if item else None

    # RC179 — Restore validation
    def validate_restore(
        self,
        *,
        export_id: str,
        expected_record_count: int | None = None,
    ) -> dict[str, Any]:
        export = self._backup_exports.get(export_id)

        if export is None:
            return {
                "valid": False,
                "reason": "EXPORT_NOT_FOUND",
            }

        issues: list[str] = []

        if (
            expected_record_count is not None
            and export["record_count"]
            != expected_record_count
        ):
            issues.append(
                "RECORD_COUNT_MISMATCH"
            )

        seen_ids: set[str] = set()

        for record in export["records"]:
            deal_id = record.get("deal_id")

            if not deal_id:
                issues.append(
                    "MISSING_DEAL_ID"
                )
                continue

            if deal_id in seen_ids:
                issues.append(
                    "DUPLICATE_DEAL_ID"
                )

            seen_ids.add(deal_id)

            if not record.get("payload_hash"):
                issues.append(
                    "MISSING_PAYLOAD_HASH"
                )

        result = {
            "validation_id": str(uuid4()),
            "export_id": export_id,
            "valid": len(issues) == 0,
            "reason": (
                "RESTORE_VALID"
                if not issues
                else "RESTORE_INVALID"
            ),
            "issues": sorted(set(issues)),
            "created_at": now_iso(),
        }

        self._restore_validations.append(
            result
        )

        return deepcopy(result)

    # RC180 — Storage health
    def record_health_sample(
        self,
        *,
        database_reachable: bool,
        pending_outbox_count: int,
        dead_letter_count: int,
        last_backup_age_hours: float | None,
        integrity_healthy: bool,
    ) -> dict[str, Any]:
        score = 100
        reasons: list[str] = []

        if not database_reachable:
            score -= 60
            reasons.append(
                "DATABASE_UNREACHABLE"
            )

        if pending_outbox_count > 1000:
            score -= 20
            reasons.append(
                "OUTBOX_BACKLOG_HIGH"
            )
        elif pending_outbox_count > 100:
            score -= 10
            reasons.append(
                "OUTBOX_BACKLOG_ELEVATED"
            )

        if dead_letter_count > 0:
            score -= min(
                20,
                dead_letter_count,
            )
            reasons.append(
                "DEAD_LETTERS_PRESENT"
            )

        if (
            last_backup_age_hours is None
            or last_backup_age_hours > 48
        ):
            score -= 15
            reasons.append(
                "BACKUP_STALE"
            )

        if not integrity_healthy:
            score -= 30
            reasons.append(
                "INTEGRITY_UNHEALTHY"
            )

        score = max(score, 0)

        if score >= 90:
            status = "HEALTHY"
        elif score >= 70:
            status = "DEGRADED"
        elif score >= 40:
            status = "UNHEALTHY"
        else:
            status = "CRITICAL"

        sample = {
            "sample_id": str(uuid4()),
            "status": status,
            "score": score,
            "reasons": reasons,
            "database_reachable": database_reachable,
            "pending_outbox_count": pending_outbox_count,
            "dead_letter_count": dead_letter_count,
            "last_backup_age_hours": last_backup_age_hours,
            "integrity_healthy": integrity_healthy,
            "created_at": now_iso(),
        }

        self._health_samples.append(sample)

        return {
            "recorded": True,
            "sample": deepcopy(sample),
            "metadata": {
                "health_version": "deal_storage_health_v1"
            },
        }

    def latest_health(self) -> dict[str, Any] | None:
        if not self._health_samples:
            return None
        return deepcopy(
            self._health_samples[-1]
        )
