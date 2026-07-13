from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class StorageProductionReadinessService:
    def __init__(self) -> None:
        self._encryption_policies: dict[str, dict[str, Any]] = {}
        self._access_events: list[dict[str, Any]] = []
        self._maintenance_windows: dict[str, dict[str, Any]] = {}
        self._readiness_reports: list[dict[str, Any]] = []

    # RC191 — Capacity planning
    def calculate_capacity_plan(
        self,
        *,
        current_storage_gb: float,
        used_storage_gb: float,
        daily_growth_gb: float,
        retention_days: int,
        safety_margin_pct: float = 25,
    ) -> dict[str, Any]:
        if current_storage_gb <= 0:
            return {
                "calculated": False,
                "reason": "INVALID_STORAGE_CAPACITY",
            }

        if used_storage_gb < 0 or daily_growth_gb < 0:
            return {
                "calculated": False,
                "reason": "INVALID_STORAGE_USAGE",
            }

        projected_growth = (
            daily_growth_gb * max(retention_days, 0)
        )

        required_without_margin = (
            used_storage_gb + projected_growth
        )

        required_with_margin = (
            required_without_margin
            * (1 + max(safety_margin_pct, 0) / 100)
        )

        free_storage = (
            current_storage_gb - used_storage_gb
        )

        days_until_full = (
            free_storage / daily_growth_gb
            if daily_growth_gb > 0
            else None
        )

        utilization_pct = (
            used_storage_gb
            / current_storage_gb
            * 100
        )

        if utilization_pct >= 90:
            status = "CRITICAL"
        elif utilization_pct >= 75:
            status = "WARNING"
        else:
            status = "HEALTHY"

        return {
            "calculated": True,
            "status": status,
            "current_storage_gb": float(
                current_storage_gb
            ),
            "used_storage_gb": float(
                used_storage_gb
            ),
            "free_storage_gb": round(
                free_storage,
                4,
            ),
            "utilization_pct": round(
                utilization_pct,
                2,
            ),
            "projected_growth_gb": round(
                projected_growth,
                4,
            ),
            "required_storage_gb": round(
                required_with_margin,
                4,
            ),
            "additional_storage_needed_gb": round(
                max(
                    required_with_margin
                    - current_storage_gb,
                    0,
                ),
                4,
            ),
            "days_until_full": (
                round(days_until_full, 2)
                if days_until_full is not None
                else None
            ),
            "metadata": {
                "capacity_version": "storage_capacity_v1"
            },
        }

    # RC192 — Encryption governance
    def register_encryption_policy(
        self,
        *,
        policy_id: str,
        encryption_at_rest: bool,
        encryption_in_transit: bool,
        key_provider: str,
        key_reference: str,
        rotation_days: int,
        enabled: bool = True,
    ) -> dict[str, Any]:
        if rotation_days <= 0:
            return {
                "registered": False,
                "reason": "INVALID_ROTATION_PERIOD",
                "policy": None,
            }

        if not key_reference.strip():
            return {
                "registered": False,
                "reason": "KEY_REFERENCE_REQUIRED",
                "policy": None,
            }

        policy = {
            "policy_id": policy_id,
            "encryption_at_rest": encryption_at_rest,
            "encryption_in_transit": encryption_in_transit,
            "key_provider": key_provider,
            "key_reference": key_reference,
            "rotation_days": rotation_days,
            "enabled": enabled,
            "registered_at": now_iso(),
        }

        self._encryption_policies[
            policy_id
        ] = policy

        return {
            "registered": True,
            "reason": "ENCRYPTION_POLICY_REGISTERED",
            "policy": deepcopy(policy),
            "metadata": {
                "encryption_version": "storage_encryption_v1"
            },
        }

    def evaluate_encryption_compliance(
        self,
        *,
        policy_id: str,
        key_age_days: int,
        tls_enabled: bool,
        volume_encrypted: bool,
    ) -> dict[str, Any]:
        policy = self._encryption_policies.get(
            policy_id
        )

        if policy is None:
            return {
                "compliant": False,
                "reason": "POLICY_NOT_FOUND",
                "issues": ["POLICY_NOT_FOUND"],
            }

        issues = []

        if (
            policy["encryption_at_rest"]
            and not volume_encrypted
        ):
            issues.append(
                "ENCRYPTION_AT_REST_MISSING"
            )

        if (
            policy["encryption_in_transit"]
            and not tls_enabled
        ):
            issues.append(
                "TLS_NOT_ENABLED"
            )

        if key_age_days > policy["rotation_days"]:
            issues.append(
                "KEY_ROTATION_OVERDUE"
            )

        return {
            "compliant": len(issues) == 0,
            "reason": (
                "ENCRYPTION_COMPLIANT"
                if not issues
                else "ENCRYPTION_NON_COMPLIANT"
            ),
            "issues": issues,
            "policy": deepcopy(policy),
        }

    # RC193 — Access audit
    def record_access_event(
        self,
        *,
        actor_id: str,
        action: str,
        resource_type: str,
        resource_id: str,
        allowed: bool,
        reason: str,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        event = {
            "access_event_id": str(uuid4()),
            "actor_id": actor_id,
            "action": action.upper(),
            "resource_type": resource_type,
            "resource_id": resource_id,
            "allowed": allowed,
            "reason": reason,
            "metadata": metadata or {},
            "created_at": now_iso(),
        }

        self._access_events.append(event)

        return {
            "recorded": True,
            "event": deepcopy(event),
            "metadata": {
                "audit_version": "storage_access_audit_v1"
            },
        }

    def query_access_events(
        self,
        *,
        actor_id: str | None = None,
        allowed: bool | None = None,
        action: str | None = None,
    ) -> dict[str, Any]:
        events = list(self._access_events)

        if actor_id is not None:
            events = [
                item
                for item in events
                if item["actor_id"] == actor_id
            ]

        if allowed is not None:
            events = [
                item
                for item in events
                if item["allowed"] is allowed
            ]

        if action is not None:
            normalized = action.upper()
            events = [
                item
                for item in events
                if item["action"] == normalized
            ]

        return {
            "event_count": len(events),
            "events": deepcopy(events),
        }

    # RC194 — Maintenance windows
    def register_maintenance_window(
        self,
        *,
        window_id: str,
        starts_at: str,
        ends_at: str,
        operation_type: str,
        allow_writes: bool,
        approved_by: str,
    ) -> dict[str, Any]:
        start = datetime.fromisoformat(
            starts_at
        )
        end = datetime.fromisoformat(
            ends_at
        )

        if end <= start:
            return {
                "registered": False,
                "reason": "INVALID_MAINTENANCE_WINDOW",
                "window": None,
            }

        window = {
            "window_id": window_id,
            "starts_at": starts_at,
            "ends_at": ends_at,
            "operation_type": operation_type,
            "allow_writes": allow_writes,
            "approved_by": approved_by,
            "status": "SCHEDULED",
            "registered_at": now_iso(),
        }

        self._maintenance_windows[
            window_id
        ] = window

        return {
            "registered": True,
            "window": deepcopy(window),
        }

    def evaluate_operation_window(
        self,
        *,
        at_time: str,
        requires_write: bool,
    ) -> dict[str, Any]:
        current = datetime.fromisoformat(
            at_time
        )

        active = [
            window
            for window in self._maintenance_windows.values()
            if datetime.fromisoformat(
                window["starts_at"]
            )
            <= current
            <= datetime.fromisoformat(
                window["ends_at"]
            )
        ]

        if not active:
            return {
                "allowed": True,
                "reason": "NO_ACTIVE_MAINTENANCE",
                "active_windows": [],
            }

        write_blocked = (
            requires_write
            and any(
                not window["allow_writes"]
                for window in active
            )
        )

        return {
            "allowed": not write_blocked,
            "reason": (
                "WRITE_BLOCKED_BY_MAINTENANCE"
                if write_blocked
                else "OPERATION_ALLOWED_DURING_MAINTENANCE"
            ),
            "active_windows": deepcopy(active),
        }

    # RC195 — Production readiness gate
    def evaluate_production_readiness(
        self,
        *,
        capacity_status: str,
        encryption_compliant: bool,
        integrity_healthy: bool,
        backup_recent: bool,
        restore_drill_successful: bool,
        slo_healthy: bool,
        pending_critical_access_issues: int,
    ) -> dict[str, Any]:
        checks = {
            "capacity": capacity_status
            in {"HEALTHY", "WARNING"},
            "encryption": encryption_compliant,
            "integrity": integrity_healthy,
            "backup": backup_recent,
            "restore_drill": restore_drill_successful,
            "slo": slo_healthy,
            "access_audit": (
                pending_critical_access_issues == 0
            ),
        }

        failed_checks = [
            name
            for name, passed in checks.items()
            if not passed
        ]

        blockers = []

        if capacity_status == "CRITICAL":
            blockers.append(
                "CAPACITY_CRITICAL"
            )

        if not encryption_compliant:
            blockers.append(
                "ENCRYPTION_NON_COMPLIANT"
            )

        if not integrity_healthy:
            blockers.append(
                "INTEGRITY_UNHEALTHY"
            )

        if not restore_drill_successful:
            blockers.append(
                "RESTORE_DRILL_FAILED"
            )

        ready = (
            len(failed_checks) == 0
            and len(blockers) == 0
        )

        report = {
            "report_id": str(uuid4()),
            "ready": ready,
            "status": (
                "READY"
                if ready
                else "NOT_READY"
            ),
            "checks": checks,
            "failed_checks": failed_checks,
            "blockers": blockers,
            "created_at": now_iso(),
        }

        self._readiness_reports.append(
            report
        )

        return {
            "evaluated": True,
            "report": deepcopy(report),
            "metadata": {
                "readiness_version": "storage_production_readiness_v1"
            },
        }

    def latest_readiness_report(
        self,
    ) -> dict[str, Any] | None:
        if not self._readiness_reports:
            return None

        return deepcopy(
            self._readiness_reports[-1]
        )
