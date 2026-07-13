from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.domains.deal_storage.sqlalchemy_repository import (
    SQLAlchemyDealStorageRepository,
)

router = APIRouter(
    prefix="/deal-storage-sql",
    tags=["deal-storage-sql"],
)


class RecordRequest(BaseModel):
    deal_id: str
    payload: dict[str, Any] = Field(
        default_factory=dict
    )
    expected_version: int | None = None
    archived: bool = False


class TransactionRequest(BaseModel):
    deal_id: str
    payload: dict[str, Any] = Field(
        default_factory=dict
    )
    expected_version: int | None = None
    event_type: str
    event_payload: dict[str, Any] = Field(
        default_factory=dict
    )


class PurgeRequest(BaseModel):
    older_than_days: int
    dry_run: bool = True


class BackupRequest(BaseModel):
    backup_name: str


@router.post("/records")
def upsert_record(
    payload: RecordRequest,
    db: Session = Depends(get_db),
):
    return SQLAlchemyDealStorageRepository(
        db
    ).upsert_record(
        **payload.model_dump()
    )


@router.get("/records/{deal_id}")
def get_record(
    deal_id: str,
    db: Session = Depends(get_db),
):
    record = SQLAlchemyDealStorageRepository(
        db
    ).get_record(deal_id)

    if record is None:
        raise HTTPException(
            status_code=404,
            detail="DEAL_RECORD_NOT_FOUND",
        )

    return record


@router.post("/transactions")
def save_transaction(
    payload: TransactionRequest,
    db: Session = Depends(get_db),
):
    return SQLAlchemyDealStorageRepository(
        db
    ).save_with_outbox(
        **payload.model_dump()
    )


@router.post("/outbox/claim")
def claim_outbox(
    limit: int = 100,
    db: Session = Depends(get_db),
):
    events = SQLAlchemyDealStorageRepository(
        db
    ).claim_pending_events(limit=limit)

    return {
        "claimed_count": len(events),
        "events": events,
    }


@router.post("/outbox/{event_id}/publish")
def publish_event(
    event_id: str,
    db: Session = Depends(get_db),
):
    event = SQLAlchemyDealStorageRepository(
        db
    ).mark_event_published(event_id)

    if event is None:
        raise HTTPException(
            status_code=404,
            detail="OUTBOX_EVENT_NOT_FOUND",
        )

    return event


@router.post("/retention/purge")
def purge_records(
    payload: PurgeRequest,
    db: Session = Depends(get_db),
):
    return SQLAlchemyDealStorageRepository(
        db
    ).purge_archived(
        older_than_days=payload.older_than_days,
        dry_run=payload.dry_run,
    )


@router.post("/integrity/audit")
def audit_integrity(
    db: Session = Depends(get_db),
):
    return SQLAlchemyDealStorageRepository(
        db
    ).audit_integrity()


@router.post("/backups")
def create_backup(
    payload: BackupRequest,
    db: Session = Depends(get_db),
):
    return SQLAlchemyDealStorageRepository(
        db
    ).create_backup_manifest(
        backup_name=payload.backup_name
    )


@router.post("/backups/{manifest_id}/verify")
def verify_backup(
    manifest_id: str,
    db: Session = Depends(get_db),
):
    return SQLAlchemyDealStorageRepository(
        db
    ).verify_backup_manifest(
        manifest_id
    )
