from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def now_iso() -> str:
    return now_utc().isoformat()


class StorageReliabilityGovernanceService:
    def __init__(self) -> None:
        self._worker_leases: dict[str, dict[str, Any]] = {}
        self._backup_catalog: dict[str, dict[str, Any]] = {}
        self._restore_approvals: dict[str, dict[str, Any]] = {}
        self._dr_plans: dict[str, dict[str, Any]] = {}
        self._slo_samples: list[dict[str, Any]] = []

    # RC186 — Worker lease and heartbeat
    def acquire_worker_lease(
        self,
        *,
        worker_id: str,
        lease_seconds: int = 60,
    ) -> dict[str, Any]:
        if lease_seconds <= 0:
            return {
                "acquired": False,
                "reason": "INVALID_LEASE_DURATION",
                "lease": None,
            }

        existing = self._worker_leases.get(worker_id)
        current = now_utc()

        if existing and datetime.fromisoformat(
            existing["expires_at"]
        ) > current:
            return {
                "acquired": False,
                "reason": "LEASE_ALREADY_ACTIVE",
                "lease": deepcopy(existing),
            }

        lease = {
            "lease_id": str(uuid4()),
            "worker_id": worker_id,
            "status": "ACTIVE",
            "acquired_at": current.isoformat(),
            "last_heartbeat_at": current.isoformat(),
            "expires_at": (
                current + timedelta(seconds=lease_seconds)
            ).isoformat(),
            "lease_seconds": lease_seconds,
        }
        self._worker_leases[worker_id] = lease

        return {
            "acquired": True,
            "reason": "LEASE_ACQUIRED",
            "lease": deepcopy(lease),
            "metadata": {
                "lease_version": "storage_worker_lease_v1"
            },
        }

    def heartbeat_worker(
        self,
        *,
        worker_id: str,
    ) -> dict[str, Any]:
        lease = self._worker_leases.get(worker_id)

        if lease is None:
            return {
                "updated": False,
                "reason": "LEASE_NOT_FOUND",
                "lease": None,
            }

        current = now_utc()

        if datetime.fromisoformat(
            lease["expires_at"]
        ) <= current:
            lease["status"] = "EXPIRED"
            return {
                "updated": False,
                "reason": "LEASE_EXPIRED",
                "lease": deepcopy(lease),
            }

        lease["last_heartbeat_at"] = current.isoformat()
        lease["expires_at"] = (
            current
            + timedelta(
                seconds=lease["lease_seconds"]
            )
        ).isoformat()

        return {
            "updated": True,
            "reason": "HEARTBEAT_RECORDED",
            "lease": deepcopy(lease),
        }

    def release_worker_lease(
        self,
        *,
        worker_id: str,
    ) -> dict[str, Any]:
        lease = self._worker_leases.get(worker_id)

        if lease is None:
            return {
                "released": False,
                "reason": "LEASE_NOT_FOUND",
            }

        lease["status"] = "RELEASED"
        lease["released_at"] = now_iso()

        return {
            "released": True,
            "lease": deepcopy(lease),
        }

    # RC187 — Backup retention policy
    def register_backup(
        self,
        *,
        backup_id: str,
        backup_name: str,
        created_at: str,
        backup_type: str = "FULL",
        protected: bool = False,
    ) -> dict[str, Any]:
        backup = {
            "backup_id": backup_id,
            "backup_name": backup_name,
            "created_at": created_at,
            "backup_type": backup_type.upper(),
            "protected": protected,
            "status": "AVAILABLE",
        }
        self._backup_catalog[backup_id] = backup

        return {
            "registered": True,
            "backup": deepcopy(backup),
        }

    def evaluate_backup_retention(
        self,
        *,
        reference_time: str,
        full_retention_days: int = 30,
        incremental_retention_days: int = 7,
    ) -> dict[str, Any]:
        reference = datetime.fromisoformat(reference_time)
        retain = []
        delete = []

        for backup in self._backup_catalog.values():
            if backup["protected"]:
                retain.append({
                    **backup,
                    "retention_reason": "PROTECTED",
                })
                continue

            created = datetime.fromisoformat(
                backup["created_at"]
            )

            days = (
                full_retention_days
                if backup["backup_type"] == "FULL"
                else incremental_retention_days
            )

            expired = created < (
                reference - timedelta(days=days)
            )

            target = delete if expired else retain
            target.append({
                **backup,
                "retention_reason": (
                    "RETENTION_EXPIRED"
                    if expired
                    else "WITHIN_RETENTION"
                ),
            })

        return {
            "retain_count": len(retain),
            "delete_count": len(delete),
            "retain": retain,
            "delete": delete,
            "metadata": {
                "retention_version": "backup_retention_v1"
            },
        }

    # RC188 — Restore approval gate
    def request_restore_approval(
        self,
        *,
        backup_id: str,
        requested_by: str,
        environment: str,
        reason: str,
    ) -> dict[str, Any]:
        approval_id = str(uuid4())
        request = {
            "approval_id": approval_id,
            "backup_id": backup_id,
            "requested_by": requested_by,
            "environment": environment.upper(),
            "reason": reason,
            "status": "PENDING",
            "approved_by": None,
            "decision_reason": None,
            "requested_at": now_iso(),
            "decided_at": None,
        }
        self._restore_approvals[
            approval_id
        ] = request

        return {
            "requested": True,
            "approval": deepcopy(request),
        }

    def decide_restore_approval(
        self,
        *,
        approval_id: str,
        approved: bool,
        decided_by: str,
        decision_reason: str,
    ) -> dict[str, Any]:
        request = self._restore_approvals.get(
            approval_id
        )

        if request is None:
            return {
                "decided": False,
                "reason": "APPROVAL_NOT_FOUND",
            }

        if request["status"] != "PENDING":
            return {
                "decided": False,
                "reason": "APPROVAL_ALREADY_DECIDED",
                "approval": deepcopy(request),
            }

        request["status"] = (
            "APPROVED"
            if approved
            else "REJECTED"
        )
        request["approved_by"] = decided_by
        request["decision_reason"] = decision_reason
        request["decided_at"] = now_iso()

        return {
            "decided": True,
            "approval": deepcopy(request),
        }

    def can_execute_restore(
        self,
        *,
        approval_id: str,
    ) -> dict[str, Any]:
        request = self._restore_approvals.get(
            approval_id
        )

        if request is None:
            return {
                "allowed": False,
                "reason": "APPROVAL_NOT_FOUND",
            }

        return {
            "allowed": request["status"] == "APPROVED",
            "reason": (
                "RESTORE_APPROVED"
                if request["status"] == "APPROVED"
                else "RESTORE_NOT_APPROVED"
            ),
            "approval": deepcopy(request),
        }

    # RC189 — Disaster recovery plan
    def create_disaster_recovery_plan(
        self,
        *,
        plan_name: str,
        rpo_minutes: int,
        rto_minutes: int,
        primary_region: str,
        recovery_region: str,
        steps: list[str],
    ) -> dict[str, Any]:
        if rpo_minutes < 0 or rto_minutes <= 0:
            return {
                "created": False,
                "reason": "INVALID_RECOVERY_OBJECTIVES",
                "plan": None,
            }

        plan_id = str(uuid4())
        plan = {
            "plan_id": plan_id,
            "plan_name": plan_name,
            "rpo_minutes": rpo_minutes,
            "rto_minutes": rto_minutes,
            "primary_region": primary_region,
            "recovery_region": recovery_region,
            "steps": list(steps),
            "status": "DRAFT",
            "last_tested_at": None,
            "last_test_successful": None,
            "created_at": now_iso(),
        }
        self._dr_plans[plan_id] = plan

        return {
            "created": True,
            "plan": deepcopy(plan),
        }

    def record_disaster_recovery_test(
        self,
        *,
        plan_id: str,
        actual_rpo_minutes: int,
        actual_rto_minutes: int,
        successful: bool,
        notes: str,
    ) -> dict[str, Any]:
        plan = self._dr_plans.get(plan_id)

        if plan is None:
            return {
                "recorded": False,
                "reason": "PLAN_NOT_FOUND",
            }

        objectives_met = (
            actual_rpo_minutes
            <= plan["rpo_minutes"]
            and actual_rto_minutes
            <= plan["rto_minutes"]
        )

        plan["last_tested_at"] = now_iso()
        plan["last_test_successful"] = (
            successful and objectives_met
        )
        plan["status"] = (
            "VALIDATED"
            if successful and objectives_met
            else "NEEDS_REMEDIATION"
        )

        return {
            "recorded": True,
            "objectives_met": objectives_met,
            "plan": deepcopy(plan),
            "test": {
                "actual_rpo_minutes": actual_rpo_minutes,
                "actual_rto_minutes": actual_rto_minutes,
                "successful": successful,
                "notes": notes,
            },
        }

    # RC190 — Storage SLO tracking
    def record_slo_sample(
        self,
        *,
        availability_pct: float,
        backup_success_pct: float,
        restore_success_pct: float,
        outbox_delivery_pct: float,
        target_availability_pct: float = 99.9,
        target_backup_success_pct: float = 99.0,
        target_restore_success_pct: float = 95.0,
        target_outbox_delivery_pct: float = 99.0,
    ) -> dict[str, Any]:
        objectives = {
            "availability": {
                "actual": availability_pct,
                "target": target_availability_pct,
            },
            "backup_success": {
                "actual": backup_success_pct,
                "target": target_backup_success_pct,
            },
            "restore_success": {
                "actual": restore_success_pct,
                "target": target_restore_success_pct,
            },
            "outbox_delivery": {
                "actual": outbox_delivery_pct,
                "target": target_outbox_delivery_pct,
            },
        }

        breaches = [
            name
            for name, values in objectives.items()
            if values["actual"] < values["target"]
        ]

        sample = {
            "sample_id": str(uuid4()),
            "objectives": objectives,
            "breach_count": len(breaches),
            "breaches": breaches,
            "healthy": len(breaches) == 0,
            "created_at": now_iso(),
        }

        self._slo_samples.append(sample)

        return {
            "recorded": True,
            "sample": deepcopy(sample),
            "metadata": {
                "slo_version": "storage_slo_v1"
            },
        }

    def latest_slo(self) -> dict[str, Any] | None:
        if not self._slo_samples:
            return None

        return deepcopy(
            self._slo_samples[-1]
        )
