from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.domains.deal_storage.resilience import (
    DealStorageResilienceService,
)

router = APIRouter(
    prefix="/deal-storage-resilience",
    tags=["deal-storage-resilience"],
)

_service = DealStorageResilienceService()


class EnqueueRequest(BaseModel):
    aggregate_id: str
    event_type: str
    payload: dict[str, Any] = Field(
        default_factory=dict
    )


class PublishFailureRequest(BaseModel):
    error: str
    max_attempts: int = 5
    base_delay_seconds: int = 30


class BackupExportRequest(BaseModel):
    backup_name: str
    records: list[dict[str, Any]] = Field(
        default_factory=list
    )
    manifests: list[dict[str, Any]] = Field(
        default_factory=list
    )


class RestoreValidationRequest(BaseModel):
    expected_record_count: int | None = None


class HealthSampleRequest(BaseModel):
    database_reachable: bool
    pending_outbox_count: int
    dead_letter_count: int
    last_backup_age_hours: float | None = None
    integrity_healthy: bool


@router.post("/clear")
def clear_resilience():
    global _service
    _service = DealStorageResilienceService()
    return {"cleared": True}


@router.post("/outbox")
def enqueue_outbox(payload: EnqueueRequest):
    return _service.enqueue_outbox(
        **payload.model_dump()
    )


@router.post("/outbox/claim")
def claim_outbox(
    limit: int = 100,
    at_time: str | None = None,
):
    return _service.claim_publish_batch(
        limit=limit,
        at_time=at_time,
    )


@router.post("/outbox/{event_id}/published")
def mark_published(event_id: str):
    return _service.mark_published(
        event_id
    )


@router.post("/outbox/{event_id}/failed")
def mark_failed(
    event_id: str,
    payload: PublishFailureRequest,
):
    return _service.mark_publish_failed(
        event_id=event_id,
        **payload.model_dump(),
    )


@router.post(
    "/dead-letters/{dead_letter_id}/replay"
)
def replay_dead_letter(
    dead_letter_id: str,
):
    return _service.replay_dead_letter(
        dead_letter_id
    )


@router.post("/backup-exports")
def create_backup_export(
    payload: BackupExportRequest,
):
    return _service.create_backup_export(
        **payload.model_dump()
    )


@router.get(
    "/backup-exports/{export_id}"
)
def get_backup_export(export_id: str):
    export = _service.get_backup_export(
        export_id
    )

    if export is None:
        raise HTTPException(
            status_code=404,
            detail="BACKUP_EXPORT_NOT_FOUND",
        )

    return export


@router.post(
    "/backup-exports/{export_id}/validate"
)
def validate_restore(
    export_id: str,
    payload: RestoreValidationRequest,
):
    return _service.validate_restore(
        export_id=export_id,
        expected_record_count=(
            payload.expected_record_count
        ),
    )


@router.post("/health")
def record_health(
    payload: HealthSampleRequest,
):
    return _service.record_health_sample(
        **payload.model_dump()
    )


@router.get("/health/latest")
def get_latest_health():
    sample = _service.latest_health()

    if sample is None:
        raise HTTPException(
            status_code=404,
            detail="HEALTH_SAMPLE_NOT_FOUND",
        )

    return sample
