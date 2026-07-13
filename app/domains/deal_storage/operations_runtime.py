from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def now_iso() -> str:
    return now_utc().isoformat()


class StorageOperationsRuntime:
    def __init__(self) -> None:
        self._worker_runs: list[dict[str, Any]] = []
        self._backup_schedules: dict[str, dict[str, Any]] = {}
        self._restore_drills: list[dict[str, Any]] = []
        self._health_snapshots: list[dict[str, Any]] = []
        self._notifications: list[dict[str, Any]] = []

    # RC181 — Outbox worker runtime
    def run_outbox_worker(
        self,
        *,
        claimed_events: list[dict[str, Any]],
        provider_results: dict[str, bool] | None = None,
    ) -> dict[str, Any]:
        provider_results = provider_results or {}
        run_id = str(uuid4())
        published = []
        failed = []

        for event in claimed_events:
            event_id = str(
                event.get("event_id")
                or event.get("id")
                or ""
            )
            success = provider_results.get(
                event_id,
                True,
            )

            result = {
                "event_id": event_id,
                "aggregate_id": event.get(
                    "aggregate_id"
                ),
                "event_type": event.get(
                    "event_type"
                ),
                "status": (
                    "PUBLISHED"
                    if success
                    else "FAILED"
                ),
            }

            if success:
                published.append(result)
            else:
                failed.append(result)

        run = {
            "run_id": run_id,
            "claimed_count": len(claimed_events),
            "published_count": len(published),
            "failed_count": len(failed),
            "published": published,
            "failed": failed,
            "status": (
                "COMPLETED"
                if not failed
                else "COMPLETED_WITH_ERRORS"
            ),
            "started_at": now_iso(),
            "completed_at": now_iso(),
        }
        self._worker_runs.append(run)

        return {
            "executed": True,
            "run": deepcopy(run),
            "metadata": {
                "worker_version": "storage_outbox_worker_v1"
            },
        }

    # RC182 — Backup scheduler
    def register_backup_schedule(
        self,
        *,
        schedule_id: str,
        backup_name_prefix: str,
        interval_hours: int,
        enabled: bool = True,
    ) -> dict[str, Any]:
        if interval_hours <= 0:
            return {
                "registered": False,
                "reason": "INVALID_INTERVAL",
                "schedule": None,
            }

        schedule = {
            "schedule_id": schedule_id,
            "backup_name_prefix": backup_name_prefix,
            "interval_hours": interval_hours,
            "enabled": enabled,
            "last_run_at": None,
            "next_run_at": (
                now_utc()
                + timedelta(hours=interval_hours)
            ).isoformat(),
            "run_count": 0,
            "created_at": now_iso(),
        }
        self._backup_schedules[
            schedule_id
        ] = schedule

        return {
            "registered": True,
            "schedule": deepcopy(schedule),
            "metadata": {
                "scheduler_version": "backup_scheduler_v1"
            },
        }

    def run_backup_schedule(
        self,
        *,
        schedule_id: str,
        record_count: int,
        manifest_hash: str,
    ) -> dict[str, Any]:
        schedule = self._backup_schedules.get(
            schedule_id
        )

        if schedule is None:
            return {
                "executed": False,
                "reason": "SCHEDULE_NOT_FOUND",
            }

        if not schedule["enabled"]:
            return {
                "executed": False,
                "reason": "SCHEDULE_DISABLED",
            }

        current = now_utc()
        schedule["run_count"] += 1
        schedule["last_run_at"] = current.isoformat()
        schedule["next_run_at"] = (
            current
            + timedelta(
                hours=schedule["interval_hours"]
            )
        ).isoformat()

        backup_name = (
            f"{schedule['backup_name_prefix']}-"
            f"{current.strftime('%Y%m%d-%H%M%S')}"
        )

        return {
            "executed": True,
            "backup": {
                "backup_name": backup_name,
                "record_count": int(record_count),
                "manifest_hash": manifest_hash,
                "created_at": current.isoformat(),
            },
            "schedule": deepcopy(schedule),
        }

    # RC183 — Restore drill
    def run_restore_drill(
        self,
        *,
        backup_name: str,
        expected_record_count: int,
        restored_record_count: int,
        integrity_healthy: bool,
        duration_ms: float,
    ) -> dict[str, Any]:
        issues = []

        if expected_record_count != restored_record_count:
            issues.append(
                "RECORD_COUNT_MISMATCH"
            )

        if not integrity_healthy:
            issues.append(
                "INTEGRITY_CHECK_FAILED"
            )

        drill = {
            "drill_id": str(uuid4()),
            "backup_name": backup_name,
            "expected_record_count": expected_record_count,
            "restored_record_count": restored_record_count,
            "integrity_healthy": integrity_healthy,
            "duration_ms": float(duration_ms),
            "successful": len(issues) == 0,
            "issues": issues,
            "created_at": now_iso(),
        }
        self._restore_drills.append(drill)

        return {
            "executed": True,
            "drill": deepcopy(drill),
            "metadata": {
                "drill_version": "restore_drill_v1"
            },
        }

    # RC184 — Health dashboard
    def build_health_dashboard(
        self,
        *,
        storage_health: dict[str, Any],
        pending_outbox_count: int,
        dead_letter_count: int,
        last_backup_age_hours: float | None,
        latest_restore_drill_successful: bool | None,
    ) -> dict[str, Any]:
        score = float(
            storage_health.get(
                "score",
                0,
            )
        )

        indicators = {
            "storage_status": storage_health.get(
                "status",
                "UNKNOWN",
            ),
            "pending_outbox_count": pending_outbox_count,
            "dead_letter_count": dead_letter_count,
            "last_backup_age_hours": last_backup_age_hours,
            "latest_restore_drill_successful": (
                latest_restore_drill_successful
            ),
        }

        risks = []

        if pending_outbox_count > 100:
            risks.append("OUTBOX_BACKLOG")

        if dead_letter_count > 0:
            risks.append("DEAD_LETTERS_PRESENT")

        if (
            last_backup_age_hours is None
            or last_backup_age_hours > 48
        ):
            risks.append("BACKUP_STALE")

        if latest_restore_drill_successful is False:
            risks.append("RESTORE_DRILL_FAILED")

        if risks:
            score = max(
                0,
                score - min(30, len(risks) * 10),
            )

        if score >= 90:
            overall_status = "HEALTHY"
        elif score >= 70:
            overall_status = "DEGRADED"
        elif score >= 40:
            overall_status = "UNHEALTHY"
        else:
            overall_status = "CRITICAL"

        snapshot = {
            "snapshot_id": str(uuid4()),
            "overall_status": overall_status,
            "score": round(score, 2),
            "indicators": indicators,
            "risks": risks,
            "created_at": now_iso(),
        }
        self._health_snapshots.append(snapshot)

        return {
            "generated": True,
            "dashboard": deepcopy(snapshot),
            "metadata": {
                "dashboard_version": "storage_health_dashboard_v1"
            },
        }

    # RC185 — Notification bridge
    def build_storage_notifications(
        self,
        *,
        dashboard: dict[str, Any],
        recipient_user_ids: list[str],
    ) -> dict[str, Any]:
        status = dashboard.get(
            "overall_status",
            "UNKNOWN",
        )
        risks = dashboard.get(
            "risks",
            [],
        )

        should_notify = status in {
            "DEGRADED",
            "UNHEALTHY",
            "CRITICAL",
        }

        notifications = []

        if should_notify:
            for user_id in recipient_user_ids:
                notification = {
                    "notification_id": str(uuid4()),
                    "user_id": user_id,
                    "channel": "in_app",
                    "title": (
                        f"Storage status: {status}"
                    ),
                    "message": (
                        "Storage operasyonlarında "
                        f"{len(risks)} risk tespit edildi."
                    ),
                    "payload": {
                        "status": status,
                        "score": dashboard.get("score"),
                        "risks": risks,
                        "dashboard_snapshot_id": (
                            dashboard.get("snapshot_id")
                        ),
                    },
                    "status": "PENDING",
                    "created_at": now_iso(),
                }
                self._notifications.append(
                    notification
                )
                notifications.append(
                    notification
                )

        return {
            "should_notify": should_notify,
            "notification_count": len(
                notifications
            ),
            "notifications": deepcopy(
                notifications
            ),
            "metadata": {
                "bridge_version": "storage_notification_bridge_v1"
            },
        }

    def list_worker_runs(self) -> dict[str, Any]:
        return {
            "run_count": len(
                self._worker_runs
            ),
            "runs": deepcopy(
                self._worker_runs
            ),
        }

    def list_notifications(self) -> dict[str, Any]:
        return {
            "notification_count": len(
                self._notifications
            ),
            "notifications": deepcopy(
                self._notifications
            ),
        }
