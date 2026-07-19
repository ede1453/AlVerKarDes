from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.core.internal_service_auth import require_internal_service_key
from app.domains.deal_persistence.service import (
    DealPersistenceService,
)

router = APIRouter(
    prefix="/deal-persistence",
    tags=["deal-persistence"],
)

_service = DealPersistenceService()


class PersistDealRequest(BaseModel):
    deal_id: str
    payload: dict[str, Any] = Field(
        default_factory=dict
    )
    expected_version: int | None = None


class SnapshotRequest(BaseModel):
    include_metadata: bool = True


class CheckpointRequest(BaseModel):
    lifecycle_status: str
    decision_version: int | None = None
    event_cursor: int = 0


class ArchiveRequest(BaseModel):
    reason: str
    actor: str = "system"


class RecoveryRequest(BaseModel):
    expected_snapshot_hash: str | None = None


@router.post("/clear")
def clear_deal_persistence(
    # AUTH-004 (ADR-006): servis-arası çağrı, X-Internal-Service-Key gerektirir.
    internal_service=Depends(require_internal_service_key),
):
    global _service
    _service = DealPersistenceService()
    return {"cleared": True}


@router.post("/records")
def persist_deal(
    payload: PersistDealRequest,
    # AUTH-004 (ADR-006): servis-arası çağrı, X-Internal-Service-Key gerektirir.
    internal_service=Depends(require_internal_service_key),
):
    return _service.persist_deal(
        **payload.model_dump()
    )


@router.get("/records/{deal_id}")
def get_record(
    deal_id: str,
    # AUTH-004 (ADR-006): servis-arası çağrı, X-Internal-Service-Key gerektirir.
    internal_service=Depends(require_internal_service_key),
):
    record = _service.get_record(deal_id)

    if record is None:
        raise HTTPException(
            status_code=404,
            detail="DEAL_RECORD_NOT_FOUND",
        )

    return record


@router.post(
    "/records/{deal_id}/snapshots"
)
def create_snapshot(
    deal_id: str,
    payload: SnapshotRequest,
    # AUTH-004 (ADR-006): servis-arası çağrı, X-Internal-Service-Key gerektirir.
    internal_service=Depends(require_internal_service_key),
):
    return _service.create_snapshot(
        deal_id=deal_id,
        include_metadata=payload.include_metadata,
    )


@router.get("/snapshots/{snapshot_id}")
def get_snapshot(
    snapshot_id: str,
    # AUTH-004 (ADR-006): servis-arası çağrı, X-Internal-Service-Key gerektirir.
    internal_service=Depends(require_internal_service_key),
):
    snapshot = _service.get_snapshot(
        snapshot_id
    )

    if snapshot is None:
        raise HTTPException(
            status_code=404,
            detail="SNAPSHOT_NOT_FOUND",
        )

    return snapshot


@router.post(
    "/records/{deal_id}/checkpoints"
)
def create_checkpoint(
    deal_id: str,
    payload: CheckpointRequest,
    # AUTH-004 (ADR-006): servis-arası çağrı, X-Internal-Service-Key gerektirir.
    internal_service=Depends(require_internal_service_key),
):
    return _service.create_checkpoint(
        deal_id=deal_id,
        **payload.model_dump(),
    )


@router.get(
    "/records/{deal_id}/checkpoints/latest"
)
def get_latest_checkpoint(
    deal_id: str,
    # AUTH-004 (ADR-006): servis-arası çağrı, X-Internal-Service-Key gerektirir.
    internal_service=Depends(require_internal_service_key),
):
    checkpoint = _service.latest_checkpoint(
        deal_id
    )

    if checkpoint is None:
        raise HTTPException(
            status_code=404,
            detail="CHECKPOINT_NOT_FOUND",
        )

    return checkpoint


@router.post(
    "/records/{deal_id}/archive"
)
def archive_deal(
    deal_id: str,
    payload: ArchiveRequest,
    # AUTH-004 (ADR-006): servis-arası çağrı, X-Internal-Service-Key gerektirir.
    internal_service=Depends(require_internal_service_key),
):
    return _service.archive_deal(
        deal_id=deal_id,
        **payload.model_dump(),
    )


@router.get("/archives")
def list_archives(
    # AUTH-004 (ADR-006): servis-arası çağrı, X-Internal-Service-Key gerektirir.
    internal_service=Depends(require_internal_service_key),
):
    return _service.list_archives()


@router.post(
    "/snapshots/{snapshot_id}/recover"
)
def recover_snapshot(
    snapshot_id: str,
    payload: RecoveryRequest,
    # AUTH-004 (ADR-006): servis-arası çağrı, X-Internal-Service-Key gerektirir.
    internal_service=Depends(require_internal_service_key),
):
    return _service.recover_from_snapshot(
        snapshot_id=snapshot_id,
        expected_snapshot_hash=(
            payload.expected_snapshot_hash
        ),
    )


@router.get("/recovery-events")
def list_recovery_events(
    deal_id: str | None = None,
    # AUTH-004 (ADR-006): servis-arası çağrı, X-Internal-Service-Key gerektirir.
    internal_service=Depends(require_internal_service_key),
):
    return _service.list_recovery_events(
        deal_id=deal_id
    )
