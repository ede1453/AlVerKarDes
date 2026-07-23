from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

from app.domains.leader_election.leader_election_store_factory import get_leader_election_store

# SCALE-009: single fixed lock key -- mirrors notification_outbox's
# _LEADER_LOCK_KEY (SCALE-002). This service manages exactly one shared
# "who is the active storage-reliability worker" role; different worker_id
# values are candidates competing for THIS one lease, not independent locks.
_STORAGE_RELIABILITY_LOCK_KEY = "storage_reliability_worker"

DEFAULT_LEASE_SECONDS = 60


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def now_iso() -> str:
    return now_utc().isoformat()


class StorageReliabilityGovernanceService:
    def __init__(self, leader_store=None) -> None:
        self._backup_catalog: dict[str, dict[str, Any]] = {}
        self._restore_approvals: dict[str, dict[str, Any]] = {}
        self._dr_plans: dict[str, dict[str, Any]] = {}
        self._slo_samples: list[dict[str, Any]] = []
        # SCALE-009: worker-lease state moved to the SAME env-driven
        # leader-election store SCALE-002 built for notification_outbox
        # (Redis-backed in prod, in-memory fallback for tests/local) --
        # get_leader_election_store() is the SCALE-001 factory pattern,
        # reused as-is (no new store code written, per Organik Gelişim
        # Kanunu -- SCALE-002 already solved this exact class of problem).
        # Before this, `_worker_leases` was a plain process-local dict:
        # two different app worker PROCESSES each believing they'd won the
        # lease for the same worker_id was a real, unfixed split-brain risk
        # -- the same class of bug SCALE-002 fixed for notification_outbox.
        self._leader_store = leader_store or get_leader_election_store()

    # RC186 — Worker lease and heartbeat
    def acquire_worker_lease(
        self,
        *,
        worker_id: str,
        lease_seconds: int = DEFAULT_LEASE_SECONDS,
    ) -> dict[str, Any]:
        if lease_seconds <= 0:
            return {
                "acquired": False,
                "reason": "INVALID_LEASE_DURATION",
                "lease": None,
            }

        result = self._leader_store.acquire(
            key=_STORAGE_RELIABILITY_LOCK_KEY,
            worker_id=worker_id,
            lease_seconds=lease_seconds,
        )

        if not result["acquired"]:
            return {
                "acquired": False,
                "reason": "LEASE_ALREADY_ACTIVE",
                "lease": {
                    "worker_id": result["leader_id"],
                    "status": "ACTIVE",
                    "expires_at": result["lease_expires_at"],
                },
            }

        return {
            "acquired": True,
            "reason": "LEASE_ACQUIRED",
            "lease": {
                "worker_id": worker_id,
                "status": "ACTIVE",
                "expires_at": result["lease_expires_at"],
                "lease_seconds": lease_seconds,
            },
            "metadata": {
                "lease_version": "storage_worker_lease_v1"
            },
        }

    def heartbeat_worker(
        self,
        *,
        worker_id: str,
        lease_seconds: int = DEFAULT_LEASE_SECONDS,
    ) -> dict[str, Any]:
        if lease_seconds <= 0:
            return {
                "updated": False,
                "reason": "INVALID_LEASE_DURATION",
                "lease": None,
            }

        result = self._leader_store.renew(
            key=_STORAGE_RELIABILITY_LOCK_KEY,
            worker_id=worker_id,
            lease_seconds=lease_seconds,
        )

        if not result["renewed"]:
            # A TTL-backed lease that expired is simply gone from the store
            # (Redis deletes it) -- there's no way to distinguish "never
            # existed" from "existed and expired" the way the old in-memory
            # version's separate EXPIRED status could, so both collapse to
            # LEASE_NOT_FOUND. A worker holding a lease that ANOTHER worker
            # has since (legitimately) taken over gets the same reason too.
            return {
                "updated": False,
                "reason": "LEASE_NOT_FOUND",
                "lease": None,
            }

        return {
            "updated": True,
            "reason": "HEARTBEAT_RECORDED",
            "lease": {
                "worker_id": worker_id,
                "status": "ACTIVE",
                "expires_at": result["lease_expires_at"],
                "lease_seconds": lease_seconds,
            },
        }

    def release_worker_lease(
        self,
        *,
        worker_id: str,
    ) -> dict[str, Any]:
        result = self._leader_store.release(
            key=_STORAGE_RELIABILITY_LOCK_KEY,
            worker_id=worker_id,
        )

        if not result["released"]:
            return {
                "released": False,
                "reason": "LEASE_NOT_FOUND",
            }

        return {
            "released": True,
            "lease": {
                "worker_id": worker_id,
                "status": "RELEASED",
                "released_at": now_iso(),
            },
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

    def clear(self) -> dict[str, Any]:
        # SCALE-009: the leader-election lease lives in the SHARED store
        # (Redis or the in-memory singleton), not on this instance -- unlike
        # the dicts below, simply constructing a fresh
        # StorageReliabilityGovernanceService() would NOT release it
        # (both the old and new instance point at the same underlying
        # store). Force-release whoever currently holds it so "clear" is a
        # genuine full reset, not just a partial one that silently leaves a
        # lease behind for the next caller to be blocked by.
        current = self._leader_store.status(_STORAGE_RELIABILITY_LOCK_KEY)
        if current.get("leader_id") is not None:
            self._leader_store.release(
                key=_STORAGE_RELIABILITY_LOCK_KEY,
                worker_id=current["leader_id"],
            )

        self._backup_catalog = {}
        self._restore_approvals = {}
        self._dr_plans = {}
        self._slo_samples = []

        return {"cleared": True}
