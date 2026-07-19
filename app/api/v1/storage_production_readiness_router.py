from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.domains.deal_storage.production_readiness import (
    StorageProductionReadinessService,
)
from app.domains.identity.dependencies import get_current_user, require_role
from app.domains.identity.models import UserRole

router = APIRouter(
    prefix="/storage-production-readiness",
    tags=["storage-production-readiness"],
)

_service = StorageProductionReadinessService()


class CapacityRequest(BaseModel):
    current_storage_gb: float
    used_storage_gb: float
    daily_growth_gb: float
    retention_days: int
    safety_margin_pct: float = 25


class EncryptionPolicyRequest(BaseModel):
    policy_id: str
    encryption_at_rest: bool
    encryption_in_transit: bool
    key_provider: str
    key_reference: str
    rotation_days: int
    enabled: bool = True


class EncryptionComplianceRequest(BaseModel):
    policy_id: str
    key_age_days: int
    tls_enabled: bool
    volume_encrypted: bool


class AccessEventRequest(BaseModel):
    actor_id: str
    action: str
    resource_type: str
    resource_id: str
    allowed: bool
    reason: str
    metadata: dict[str, Any] = Field(
        default_factory=dict
    )


class MaintenanceWindowRequest(BaseModel):
    window_id: str
    starts_at: str
    ends_at: str
    operation_type: str
    allow_writes: bool
    approved_by: str


class OperationWindowRequest(BaseModel):
    at_time: str
    requires_write: bool


class ReadinessRequest(BaseModel):
    capacity_status: str
    encryption_compliant: bool
    integrity_healthy: bool
    backup_recent: bool
    restore_drill_successful: bool
    slo_healthy: bool
    pending_critical_access_issues: int


@router.post("/clear")
def clear_readiness(
    # AUTH-006 Parça 3 (ADR-005): OPERATOR+ gerektirir.
    current_user=Depends(require_role(UserRole.OPERATOR)),
):
    global _service
    _service = StorageProductionReadinessService()
    return {"cleared": True}


@router.post("/capacity")
def calculate_capacity(
    payload: CapacityRequest,
    # AUTH-006 Parça 3 (ADR-005): OPERATOR+ gerektirir.
    current_user=Depends(require_role(UserRole.OPERATOR)),
):
    return _service.calculate_capacity_plan(
        **payload.model_dump()
    )


@router.post("/encryption-policies")
def register_encryption_policy(
    payload: EncryptionPolicyRequest,
    # AUTH-006 Parça 3 (ADR-005): OPERATOR+ gerektirir.
    current_user=Depends(require_role(UserRole.OPERATOR)),
):
    return _service.register_encryption_policy(
        **payload.model_dump()
    )


@router.post("/encryption-compliance")
def evaluate_encryption(
    payload: EncryptionComplianceRequest,
    # AUTH-006 Parça 3 (ADR-005): OPERATOR+ gerektirir.
    current_user=Depends(require_role(UserRole.OPERATOR)),
):
    return _service.evaluate_encryption_compliance(
        **payload.model_dump()
    )


@router.post("/access-events")
def record_access_event(
    payload: AccessEventRequest,
    # AUTH-006 Parça 3 (ADR-005): OPERATOR+ gerektirir.
    current_user=Depends(require_role(UserRole.OPERATOR)),
):
    return _service.record_access_event(
        **payload.model_dump()
    )


@router.get("/access-events")
def query_access_events(
    actor_id: str | None = None,
    allowed: bool | None = None,
    action: str | None = None,
    # AUTH-006 Parça 3 (ADR-005): OPERATOR+ gerektirir.
    current_user=Depends(require_role(UserRole.OPERATOR)),
):
    return _service.query_access_events(
        actor_id=actor_id,
        allowed=allowed,
        action=action,
    )


@router.post("/maintenance-windows")
def register_maintenance_window(
    payload: MaintenanceWindowRequest,
    # AUTH-006 Parça 3 (ADR-005): OPERATOR+ gerektirir.
    current_user=Depends(require_role(UserRole.OPERATOR)),
):
    return _service.register_maintenance_window(
        **payload.model_dump()
    )


@router.post("/maintenance-windows/evaluate")
def evaluate_maintenance_window(
    payload: OperationWindowRequest,
    # AUTH-006 Parça 3 (ADR-005): OPERATOR+ gerektirir.
    current_user=Depends(require_role(UserRole.OPERATOR)),
):
    return _service.evaluate_operation_window(
        **payload.model_dump()
    )


@router.post("/readiness")
def evaluate_readiness(
    payload: ReadinessRequest,
    # AUTH-006 Parça 3 (ADR-005): OPERATOR+ gerektirir.
    current_user=Depends(require_role(UserRole.OPERATOR)),
):
    return _service.evaluate_production_readiness(
        **payload.model_dump()
    )


@router.get("/readiness/latest")
def get_latest_readiness(
    # AUTH-006 Parça 3 (ADR-005): OPERATOR+ gerektirir.
    current_user=Depends(require_role(UserRole.OPERATOR)),
):
    report = _service.latest_readiness_report()

    if report is None:
        raise HTTPException(
            status_code=404,
            detail="READINESS_REPORT_NOT_FOUND",
        )

    return report
