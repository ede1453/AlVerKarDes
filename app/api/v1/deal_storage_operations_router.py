from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.domains.deal_storage.operations_runtime import (
    StorageOperationsRuntime,
)
from app.domains.identity.dependencies import get_current_user, require_role
from app.domains.identity.models import UserRole

router = APIRouter(
    prefix="/deal-storage-operations",
    tags=["deal-storage-operations"],
)

_service = StorageOperationsRuntime()


class WorkerRunRequest(BaseModel):
    claimed_events: list[dict[str, Any]] = Field(
        default_factory=list
    )
    provider_results: dict[str, bool] = Field(
        default_factory=dict
    )


class BackupScheduleRequest(BaseModel):
    schedule_id: str
    backup_name_prefix: str
    interval_hours: int
    enabled: bool = True


class BackupRunRequest(BaseModel):
    record_count: int
    manifest_hash: str


class RestoreDrillRequest(BaseModel):
    backup_name: str
    expected_record_count: int
    restored_record_count: int
    integrity_healthy: bool
    duration_ms: float


class DashboardRequest(BaseModel):
    storage_health: dict[str, Any] = Field(
        default_factory=dict
    )
    pending_outbox_count: int
    dead_letter_count: int
    last_backup_age_hours: float | None = None
    latest_restore_drill_successful: bool | None = None


class NotificationBridgeRequest(BaseModel):
    dashboard: dict[str, Any] = Field(
        default_factory=dict
    )
    recipient_user_ids: list[str] = Field(
        default_factory=list
    )


@router.post("/clear")
def clear_operations(
    # AUTH-006 Parça 3 (ADR-005): OPERATOR+ gerektirir.
    current_user=Depends(require_role(UserRole.OPERATOR)),
):
    global _service
    _service = StorageOperationsRuntime()
    return {"cleared": True}


@router.post("/worker/run")
def run_worker(
    payload: WorkerRunRequest,
    # AUTH-006 Parça 3 (ADR-005): OPERATOR+ gerektirir.
    current_user=Depends(require_role(UserRole.OPERATOR)),
):
    return _service.run_outbox_worker(
        **payload.model_dump()
    )


@router.get("/worker/runs")
def list_worker_runs(
    # AUTH-006 Parça 3 (ADR-005): OPERATOR+ gerektirir.
    current_user=Depends(require_role(UserRole.OPERATOR)),
):
    return _service.list_worker_runs()


@router.post("/backup-schedules")
def register_backup_schedule(
    payload: BackupScheduleRequest,
    # AUTH-006 Parça 3 (ADR-005): OPERATOR+ gerektirir.
    current_user=Depends(require_role(UserRole.OPERATOR)),
):
    return _service.register_backup_schedule(
        **payload.model_dump()
    )


@router.post(
    "/backup-schedules/{schedule_id}/run"
)
def run_backup_schedule(
    schedule_id: str,
    payload: BackupRunRequest,
    # AUTH-006 Parça 3 (ADR-005): OPERATOR+ gerektirir.
    current_user=Depends(require_role(UserRole.OPERATOR)),
):
    return _service.run_backup_schedule(
        schedule_id=schedule_id,
        **payload.model_dump(),
    )


@router.post("/restore-drills")
def run_restore_drill(
    payload: RestoreDrillRequest,
    # AUTH-006 Parça 3 (ADR-005): OPERATOR+ gerektirir.
    current_user=Depends(require_role(UserRole.OPERATOR)),
):
    return _service.run_restore_drill(
        **payload.model_dump()
    )


@router.post("/health-dashboard")
def build_health_dashboard(
    payload: DashboardRequest,
    # AUTH-006 Parça 3 (ADR-005): OPERATOR+ gerektirir.
    current_user=Depends(require_role(UserRole.OPERATOR)),
):
    return _service.build_health_dashboard(
        **payload.model_dump()
    )


@router.post("/notification-bridge")
def build_notifications(
    payload: NotificationBridgeRequest,
    # AUTH-006 Parça 3 (ADR-005): OPERATOR+ gerektirir.
    current_user=Depends(require_role(UserRole.OPERATOR)),
):
    return _service.build_storage_notifications(
        **payload.model_dump()
    )


@router.get("/notifications")
def list_notifications(
    # AUTH-006 Parça 3 (ADR-005): OPERATOR+ gerektirir.
    current_user=Depends(require_role(UserRole.OPERATOR)),
):
    return _service.list_notifications()
