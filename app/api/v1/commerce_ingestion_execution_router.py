from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.core.internal_service_auth import require_internal_service_key
from app.domains.commerce_ingestion.execution import (
    FeedExecutionService,
)

router = APIRouter(
    prefix="/commerce-ingestion-execution",
    tags=["commerce-ingestion-execution"],
)

_service = FeedExecutionService()


class JobCreateRequest(BaseModel):
    source_id: str
    adapter_type: str
    requested_by: str


class JobExecuteRequest(BaseModel):
    content: str


@router.post("/clear")
def clear_state(
    # AUTH-004 (ADR-006): servis-arası çağrı, X-Internal-Service-Key gerektirir.
    internal_service=Depends(require_internal_service_key),
):
    global _service
    _service = FeedExecutionService()
    return {"cleared": True}


@router.post("/jobs")
def create_job(
    payload: JobCreateRequest,
    # AUTH-004 (ADR-006): servis-arası çağrı, X-Internal-Service-Key gerektirir.
    internal_service=Depends(require_internal_service_key),
):
    return _service.create_job(
        source_id=payload.source_id,
        adapter_type=payload.adapter_type,
        requested_by=payload.requested_by,
    )


@router.post("/jobs/{job_id}/execute")
def execute_job(
    job_id: str,
    payload: JobExecuteRequest,
    # AUTH-004 (ADR-006): servis-arası çağrı, X-Internal-Service-Key gerektirir.
    internal_service=Depends(require_internal_service_key),
):
    return _service.execute_job(
        job_id=job_id,
        content=payload.content,
    )


@router.get("/jobs")
def list_jobs(
    source_id: str | None = None,
    status: str | None = None,
    # AUTH-004 (ADR-006): servis-arası çağrı, X-Internal-Service-Key gerektirir.
    internal_service=Depends(require_internal_service_key),
):
    jobs = _service.repository.list_jobs(
        source_id=source_id,
        status=status,
    )
    return {
        "job_count": len(jobs),
        "jobs": jobs,
    }


@router.get("/quarantine")
def list_quarantine(
    source_id: str | None = None,
    replayed: bool | None = None,
    # AUTH-004 (ADR-006): servis-arası çağrı, X-Internal-Service-Key gerektirir.
    internal_service=Depends(require_internal_service_key),
):
    items = _service.repository.list_quarantine(
        source_id=source_id,
        replayed=replayed,
    )
    return {
        "quarantine_count": len(items),
        "items": items,
    }


@router.post("/quarantine/{quarantine_id}/replay")
def replay_quarantine(
    quarantine_id: str,
    # AUTH-004 (ADR-006): servis-arası çağrı, X-Internal-Service-Key gerektirir.
    internal_service=Depends(require_internal_service_key),
):
    return _service.replay_quarantine(
        quarantine_id=quarantine_id
    )
