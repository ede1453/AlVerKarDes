from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.core.internal_service_auth import require_internal_service_key
from app.domains.deal_storage.service import (
    DealStorageOperationsService,
)

router = APIRouter(
    prefix="/deal-storage",
    tags=["deal-storage"],
)

_service = DealStorageOperationsService()


class UpsertRequest(BaseModel):
    deal_id: str
    payload: dict[str, Any] = Field(default_factory=dict)
    version: int
    archived: bool = False
    persisted_at: str | None = None


class TransactionRequest(BaseModel):
    deal_id: str
    payload: dict[str, Any] = Field(default_factory=dict)
    version: int
    event_type: str
    event_payload: dict[str, Any] = Field(default_factory=dict)


class PurgeRequest(BaseModel):
    older_than_days: int
    reference_time: str | None = None
    dry_run: bool = True


class BackupRequest(BaseModel):
    backup_name: str


@router.post("/clear")
def clear_storage(
    # AUTH-004 (ADR-006): servis-arası çağrı, X-Internal-Service-Key gerektirir.
    internal_service=Depends(require_internal_service_key),
):
    global _service
    _service = DealStorageOperationsService()
    return {"cleared": True}


@router.post("/records")
def upsert_record(
    payload: UpsertRequest,
    # AUTH-004 (ADR-006): servis-arası çağrı, X-Internal-Service-Key gerektirir.
    internal_service=Depends(require_internal_service_key),
):
    return _service.repository.upsert(
        **payload.model_dump()
    )


@router.get("/records/{deal_id}")
def get_record(
    deal_id: str,
    # AUTH-004 (ADR-006): servis-arası çağrı, X-Internal-Service-Key gerektirir.
    internal_service=Depends(require_internal_service_key),
):
    record = _service.repository.get(deal_id)
    if record is None:
        raise HTTPException(
            status_code=404,
            detail="DEAL_RECORD_NOT_FOUND",
        )
    return record


@router.post("/transactions")
def save_transaction(
    payload: TransactionRequest,
    # AUTH-004 (ADR-006): servis-arası çağrı, X-Internal-Service-Key gerektirir.
    internal_service=Depends(require_internal_service_key),
):
    return _service.repository.save_with_outbox(
        **payload.model_dump()
    )


@router.get("/outbox")
def list_outbox(
    status: str | None = None,
    # AUTH-004 (ADR-006): servis-arası çağrı, X-Internal-Service-Key gerektirir.
    internal_service=Depends(require_internal_service_key),
):
    events = _service.repository.list_outbox(
        status=status
    )
    return {
        "event_count": len(events),
        "events": events,
    }


@router.post("/outbox/{event_id}/publish")
def publish_outbox(
    event_id: str,
    # AUTH-004 (ADR-006): servis-arası çağrı, X-Internal-Service-Key gerektirir.
    internal_service=Depends(require_internal_service_key),
):
    event = _service.repository.mark_outbox_published(
        event_id
    )
    if event is None:
        raise HTTPException(
            status_code=404,
            detail="OUTBOX_EVENT_NOT_FOUND",
        )
    return event


@router.post("/retention/purge")
def purge_records(
    payload: PurgeRequest,
    # AUTH-004 (ADR-006): servis-arası çağrı, X-Internal-Service-Key gerektirir.
    internal_service=Depends(require_internal_service_key),
):
    return _service.repository.purge_archived(
        **payload.model_dump()
    )


@router.post("/integrity/audit")
def audit_integrity(
    # AUTH-004 (ADR-006): servis-arası çağrı, X-Internal-Service-Key gerektirir.
    internal_service=Depends(require_internal_service_key),
):
    return _service.repository.audit_integrity()


@router.post("/backups")
def create_backup(
    payload: BackupRequest,
    # AUTH-004 (ADR-006): servis-arası çağrı, X-Internal-Service-Key gerektirir.
    internal_service=Depends(require_internal_service_key),
):
    return _service.repository.create_backup_manifest(
        backup_name=payload.backup_name
    )


@router.post("/backups/{manifest_id}/verify")
def verify_backup(
    manifest_id: str,
    # AUTH-004 (ADR-006): servis-arası çağrı, X-Internal-Service-Key gerektirir.
    internal_service=Depends(require_internal_service_key),
):
    return _service.repository.verify_backup_manifest(
        manifest_id
    )
