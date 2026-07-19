from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.domains.commerce_ingestion.connector_readiness import build_connector_readiness
from app.domains.commerce_ingestion.operations import (
    ConnectorOperationsService,
)
from app.domains.identity.dependencies import get_current_user, require_role
from app.domains.identity.models import UserRole

router = APIRouter(
    prefix="/connector-operations",
    tags=["connector-operations"],
)

_service = ConnectorOperationsService()


class CredentialProfileRequest(BaseModel):
    profile_id: str
    provider: str
    secret_reference: str
    enabled: bool = True
    metadata: dict[str, Any] = Field(
        default_factory=dict
    )


class ValidationRequest(BaseModel):
    items: list[dict[str, Any]]


class RetryRequest(BaseModel):
    operation_key: str
    max_attempts: int = 5
    base_delay_seconds: int = 30
    multiplier: float = 2.0


class ScheduleRequest(BaseModel):
    schedule_id: str
    source_id: str
    interval_minutes: int
    enabled: bool = True


class MetricsRequest(BaseModel):
    source_id: str
    collected_count: int
    ingested_count: int
    failed_count: int
    duration_ms: float


@router.get("/readiness")
def get_connector_readiness(
    # AUTH-006 Parça 3 (ADR-005): OPERATOR+ gerektirir.
    current_user=Depends(require_role(UserRole.OPERATOR)),
):
    return build_connector_readiness()


@router.post("/clear")
def clear_connector_operations(
    # AUTH-006 Parça 3 (ADR-005): OPERATOR+ gerektirir.
    current_user=Depends(require_role(UserRole.OPERATOR)),
):
    global _service
    _service = ConnectorOperationsService()
    return {"cleared": True}


@router.post("/credential-profiles")
def register_credential_profile(
    payload: CredentialProfileRequest,
    # AUTH-006 Parça 3 (ADR-005): OPERATOR+ gerektirir.
    current_user=Depends(require_role(UserRole.OPERATOR)),
):
    return _service.register_credential_profile(
        **payload.model_dump()
    )


@router.get("/credential-profiles/{profile_id}")
def get_credential_profile(
    profile_id: str,
    # AUTH-006 Parça 3 (ADR-005): OPERATOR+ gerektirir.
    current_user=Depends(require_role(UserRole.OPERATOR)),
):
    profile = _service.get_credential_profile(
        profile_id
    )
    if profile is None:
        raise HTTPException(
            status_code=404,
            detail="CREDENTIAL_PROFILE_NOT_FOUND",
        )
    return profile


@router.post("/validate-items")
def validate_items(
    payload: ValidationRequest,
    # AUTH-006 Parça 3 (ADR-005): OPERATOR+ gerektirir.
    current_user=Depends(require_role(UserRole.OPERATOR)),
):
    return _service.validate_source_items(
        payload.items
    )


@router.post("/retry")
def schedule_retry(
    payload: RetryRequest,
    # AUTH-006 Parça 3 (ADR-005): OPERATOR+ gerektirir.
    current_user=Depends(require_role(UserRole.OPERATOR)),
):
    return _service.calculate_retry(
        **payload.model_dump()
    )


@router.post("/retry/{operation_key}/reset")
def reset_retry(
    operation_key: str,
    # AUTH-006 Parça 3 (ADR-005): OPERATOR+ gerektirir.
    current_user=Depends(require_role(UserRole.OPERATOR)),
):
    return _service.reset_retry(operation_key)


@router.post("/schedules")
def register_schedule(
    payload: ScheduleRequest,
    # AUTH-006 Parça 3 (ADR-005): OPERATOR+ gerektirir.
    current_user=Depends(require_role(UserRole.OPERATOR)),
):
    return _service.register_schedule(
        **payload.model_dump()
    )


@router.post("/schedules/{schedule_id}/mark-run")
def mark_schedule_run(
    schedule_id: str,
    # AUTH-006 Parça 3 (ADR-005): OPERATOR+ gerektirir.
    current_user=Depends(require_role(UserRole.OPERATOR)),
):
    return _service.mark_schedule_run(
        schedule_id
    )


@router.get("/schedules/due")
def list_due_schedules(
    at_time: str | None = None,
    # AUTH-006 Parça 3 (ADR-005): OPERATOR+ gerektirir.
    current_user=Depends(require_role(UserRole.OPERATOR)),
):
    return _service.list_due_schedules(
        at_time=at_time
    )


@router.post("/metrics")
def record_metrics(
    payload: MetricsRequest,
    # AUTH-006 Parça 3 (ADR-005): OPERATOR+ gerektirir.
    current_user=Depends(require_role(UserRole.OPERATOR)),
):
    return _service.record_run_metrics(
        **payload.model_dump()
    )


@router.get("/metrics/{source_id}")
def get_metrics(
    source_id: str,
    # AUTH-006 Parça 3 (ADR-005): OPERATOR+ gerektirir.
    current_user=Depends(require_role(UserRole.OPERATOR)),
):
    return _service.get_metrics(source_id)
