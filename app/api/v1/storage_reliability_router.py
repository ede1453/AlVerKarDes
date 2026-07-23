from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.domains.deal_storage.reliability_governance import (
    StorageReliabilityGovernanceService,
)
from app.domains.identity.dependencies import get_current_user, require_role
from app.domains.identity.models import UserRole

router = APIRouter(
    prefix="/storage-reliability",
    tags=["storage-reliability"],
)

_service = StorageReliabilityGovernanceService()


class LeaseRequest(BaseModel):
    worker_id: str
    lease_seconds: int = 60


class BackupRegistrationRequest(BaseModel):
    backup_id: str
    backup_name: str
    created_at: str
    backup_type: str = "FULL"
    protected: bool = False


class RetentionRequest(BaseModel):
    reference_time: str
    full_retention_days: int = 30
    incremental_retention_days: int = 7


class RestoreApprovalRequest(BaseModel):
    backup_id: str
    requested_by: str
    environment: str
    reason: str


class RestoreDecisionRequest(BaseModel):
    approved: bool
    decided_by: str
    decision_reason: str


class DRPlanRequest(BaseModel):
    plan_name: str
    rpo_minutes: int
    rto_minutes: int
    primary_region: str
    recovery_region: str
    steps: list[str] = Field(default_factory=list)


class DRTestRequest(BaseModel):
    actual_rpo_minutes: int
    actual_rto_minutes: int
    successful: bool
    notes: str


class SLOSampleRequest(BaseModel):
    availability_pct: float
    backup_success_pct: float
    restore_success_pct: float
    outbox_delivery_pct: float
    target_availability_pct: float = 99.9
    target_backup_success_pct: float = 99.0
    target_restore_success_pct: float = 95.0
    target_outbox_delivery_pct: float = 99.0


@router.post("/clear")
def clear_reliability(
    # AUTH-006 Parça 3 (ADR-005): OPERATOR+ gerektirir.
    current_user=Depends(require_role(UserRole.OPERATOR)),
):
    # SCALE-009: the worker-lease now lives in a store SHARED across
    # StorageReliabilityGovernanceService instances (Redis or the in-memory
    # singleton) -- reassigning `_service` to a fresh instance no longer
    # releases it, so `clear()` explicitly force-releases whoever holds it.
    return _service.clear()


@router.post("/worker-leases")
def acquire_lease(
    payload: LeaseRequest,
    # AUTH-006 Parça 3 (ADR-005): OPERATOR+ gerektirir.
    current_user=Depends(require_role(UserRole.OPERATOR)),
):
    return _service.acquire_worker_lease(
        **payload.model_dump()
    )


@router.post(
    "/worker-leases/{worker_id}/heartbeat"
)
def heartbeat(
    worker_id: str,
    lease_seconds: int = 60,
    # AUTH-006 Parça 3 (ADR-005): OPERATOR+ gerektirir.
    current_user=Depends(require_role(UserRole.OPERATOR)),
):
    return _service.heartbeat_worker(
        worker_id=worker_id,
        lease_seconds=lease_seconds,
    )


@router.post(
    "/worker-leases/{worker_id}/release"
)
def release(
    worker_id: str,
    # AUTH-006 Parça 3 (ADR-005): OPERATOR+ gerektirir.
    current_user=Depends(require_role(UserRole.OPERATOR)),
):
    return _service.release_worker_lease(
        worker_id=worker_id
    )


@router.post("/backups")
def register_backup(
    payload: BackupRegistrationRequest,
    # AUTH-006 Parça 3 (ADR-005): OPERATOR+ gerektirir.
    current_user=Depends(require_role(UserRole.OPERATOR)),
):
    return _service.register_backup(
        **payload.model_dump()
    )


@router.post("/backups/retention-evaluate")
def evaluate_retention(
    payload: RetentionRequest,
    # AUTH-006 Parça 3 (ADR-005): OPERATOR+ gerektirir.
    current_user=Depends(require_role(UserRole.OPERATOR)),
):
    return _service.evaluate_backup_retention(
        **payload.model_dump()
    )


@router.post("/restore-approvals")
def request_restore(
    payload: RestoreApprovalRequest,
    # AUTH-006 Parça 3 (ADR-005): OPERATOR+ gerektirir.
    current_user=Depends(require_role(UserRole.OPERATOR)),
):
    return _service.request_restore_approval(
        **payload.model_dump()
    )


@router.post(
    "/restore-approvals/{approval_id}/decision"
)
def decide_restore(
    approval_id: str,
    payload: RestoreDecisionRequest,
    # AUTH-006 Parça 3 (ADR-005): OPERATOR+ gerektirir.
    current_user=Depends(require_role(UserRole.OPERATOR)),
):
    return _service.decide_restore_approval(
        approval_id=approval_id,
        **payload.model_dump(),
    )


@router.get(
    "/restore-approvals/{approval_id}/can-execute"
)
def can_execute_restore(
    approval_id: str,
    # AUTH-006 Parça 3 (ADR-005): OPERATOR+ gerektirir.
    current_user=Depends(require_role(UserRole.OPERATOR)),
):
    return _service.can_execute_restore(
        approval_id=approval_id
    )


@router.post("/dr-plans")
def create_dr_plan(
    payload: DRPlanRequest,
    # AUTH-006 Parça 3 (ADR-005): OPERATOR+ gerektirir.
    current_user=Depends(require_role(UserRole.OPERATOR)),
):
    return _service.create_disaster_recovery_plan(
        **payload.model_dump()
    )


@router.post("/dr-plans/{plan_id}/tests")
def record_dr_test(
    plan_id: str,
    payload: DRTestRequest,
    # AUTH-006 Parça 3 (ADR-005): OPERATOR+ gerektirir.
    current_user=Depends(require_role(UserRole.OPERATOR)),
):
    return _service.record_disaster_recovery_test(
        plan_id=plan_id,
        **payload.model_dump(),
    )


@router.post("/slo-samples")
def record_slo_sample(
    payload: SLOSampleRequest,
    # AUTH-006 Parça 3 (ADR-005): OPERATOR+ gerektirir.
    current_user=Depends(require_role(UserRole.OPERATOR)),
):
    return _service.record_slo_sample(
        **payload.model_dump()
    )


@router.get("/slo-samples/latest")
def get_latest_slo(
    # AUTH-006 Parça 3 (ADR-005): OPERATOR+ gerektirir.
    current_user=Depends(require_role(UserRole.OPERATOR)),
):
    sample = _service.latest_slo()

    if sample is None:
        raise HTTPException(
            status_code=404,
            detail="SLO_SAMPLE_NOT_FOUND",
        )

    return sample
