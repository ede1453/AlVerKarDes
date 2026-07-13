from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.domains.commerce_ingestion.operations import (
    ConnectorOperationsService,
)

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


@router.post("/clear")
def clear_connector_operations():
    global _service
    _service = ConnectorOperationsService()
    return {"cleared": True}


@router.post("/credential-profiles")
def register_credential_profile(
    payload: CredentialProfileRequest,
):
    return _service.register_credential_profile(
        **payload.model_dump()
    )


@router.get("/credential-profiles/{profile_id}")
def get_credential_profile(profile_id: str):
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
def validate_items(payload: ValidationRequest):
    return _service.validate_source_items(
        payload.items
    )


@router.post("/retry")
def schedule_retry(payload: RetryRequest):
    return _service.calculate_retry(
        **payload.model_dump()
    )


@router.post("/retry/{operation_key}/reset")
def reset_retry(operation_key: str):
    return _service.reset_retry(operation_key)


@router.post("/schedules")
def register_schedule(payload: ScheduleRequest):
    return _service.register_schedule(
        **payload.model_dump()
    )


@router.post("/schedules/{schedule_id}/mark-run")
def mark_schedule_run(schedule_id: str):
    return _service.mark_schedule_run(
        schedule_id
    )


@router.get("/schedules/due")
def list_due_schedules(
    at_time: str | None = None,
):
    return _service.list_due_schedules(
        at_time=at_time
    )


@router.post("/metrics")
def record_metrics(payload: MetricsRequest):
    return _service.record_run_metrics(
        **payload.model_dump()
    )


@router.get("/metrics/{source_id}")
def get_metrics(source_id: str):
    return _service.get_metrics(source_id)
