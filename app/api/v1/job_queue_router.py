from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.core.internal_service_auth import require_internal_service_key
from app.domains.jobs.job_queue_service import JobQueueService


class JobCreateRequest(BaseModel):
    job_type: str
    payload: dict = Field(default_factory=dict)


router = APIRouter(prefix="/jobs", tags=["jobs"])

_service = JobQueueService()


@router.post("/enqueue")
async def enqueue_job(
    payload: JobCreateRequest,
    # AUTH-004 (ADR-006): servis-arası çağrı, X-Internal-Service-Key gerektirir.
    internal_service=Depends(require_internal_service_key),
):
    return _service.enqueue(payload.model_dump())


@router.post("/run-now")
async def run_job_now(
    payload: JobCreateRequest,
    # AUTH-004 (ADR-006): servis-arası çağrı, X-Internal-Service-Key gerektirir.
    internal_service=Depends(require_internal_service_key),
):
    return _service.run_now(payload.model_dump())


@router.get("")
async def list_jobs(
    limit: int = Query(default=20, ge=1, le=100),
    # AUTH-004 (ADR-006): servis-arası çağrı, X-Internal-Service-Key gerektirir.
    internal_service=Depends(require_internal_service_key),
):
    return {
        "items": _service.list_recent(limit=limit),
        "limit": limit,
    }


@router.get("/{job_id}")
async def get_job(
    job_id: str,
    # AUTH-004 (ADR-006): servis-arası çağrı, X-Internal-Service-Key gerektirir.
    internal_service=Depends(require_internal_service_key),
):
    result = _service.get(job_id)
    if result is None:
        raise HTTPException(status_code=404, detail="job_not_found")
    return result
