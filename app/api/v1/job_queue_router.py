from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.internal_service_auth import require_internal_service_key
from app.domains.jobs.job_queue_service import DEFAULT_STALE_LOCK_SECONDS, JobQueueService
from app.domains.jobs.job_repository import JobDBRepository


class JobCreateRequest(BaseModel):
    job_type: str
    payload: dict = Field(default_factory=dict)


class JobClaimRequest(BaseModel):
    worker_id: str
    stale_lock_seconds: int = DEFAULT_STALE_LOCK_SECONDS


class JobCompleteRequest(BaseModel):
    result: dict = Field(default_factory=dict)


class JobFailRequest(BaseModel):
    error: str


router = APIRouter(prefix="/jobs", tags=["jobs"])


def _service(db: AsyncSession) -> JobQueueService:
    # SCALE-003: Postgres-backed now (JobDBRepository) -- same per-request
    # construction pattern as WatchlistItemDBRepository (CLIENT-002e). No
    # more module-level singleton: a shared instance can't hold a
    # request-scoped AsyncSession, and claim_next()'s SELECT FOR UPDATE SKIP
    # LOCKED needs a real transaction per request anyway.
    return JobQueueService(repository=JobDBRepository(db))


@router.post("/enqueue")
async def enqueue_job(
    payload: JobCreateRequest,
    db: AsyncSession = Depends(get_db),
    # AUTH-004 (ADR-006): servis-arası çağrı, X-Internal-Service-Key gerektirir.
    internal_service=Depends(require_internal_service_key),
):
    return await _service(db).enqueue(payload.model_dump())


@router.post("/run-now")
async def run_job_now(
    payload: JobCreateRequest,
    db: AsyncSession = Depends(get_db),
    # AUTH-004 (ADR-006): servis-arası çağrı, X-Internal-Service-Key gerektirir.
    internal_service=Depends(require_internal_service_key),
):
    return await _service(db).run_now(payload.model_dump())


@router.post("/claim-next")
async def claim_next_job(
    payload: JobClaimRequest,
    db: AsyncSession = Depends(get_db),
    # AUTH-004 (ADR-006): servis-arası çağrı, X-Internal-Service-Key gerektirir.
    internal_service=Depends(require_internal_service_key),
):
    job = await _service(db).claim_next(
        worker_id=payload.worker_id,
        stale_lock_seconds=payload.stale_lock_seconds,
    )
    return {"job": job}


@router.post("/{job_id}/complete")
async def complete_job(
    job_id: str,
    payload: JobCompleteRequest,
    db: AsyncSession = Depends(get_db),
    # AUTH-004 (ADR-006): servis-arası çağrı, X-Internal-Service-Key gerektirir.
    internal_service=Depends(require_internal_service_key),
):
    result = await _service(db).complete(job_id, payload.result)
    if result is None:
        raise HTTPException(status_code=404, detail="job_not_found")
    return result


@router.post("/{job_id}/fail")
async def fail_job(
    job_id: str,
    payload: JobFailRequest,
    db: AsyncSession = Depends(get_db),
    # AUTH-004 (ADR-006): servis-arası çağrı, X-Internal-Service-Key gerektirir.
    internal_service=Depends(require_internal_service_key),
):
    result = await _service(db).fail(job_id, payload.error)
    if result is None:
        raise HTTPException(status_code=404, detail="job_not_found")
    return result


@router.get("")
async def list_jobs(
    limit: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    # AUTH-004 (ADR-006): servis-arası çağrı, X-Internal-Service-Key gerektirir.
    internal_service=Depends(require_internal_service_key),
):
    return {
        "items": await _service(db).list_recent(limit=limit),
        "limit": limit,
    }


@router.get("/{job_id}")
async def get_job(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    # AUTH-004 (ADR-006): servis-arası çağrı, X-Internal-Service-Key gerektirir.
    internal_service=Depends(require_internal_service_key),
):
    result = await _service(db).get(job_id)
    if result is None:
        raise HTTPException(status_code=404, detail="job_not_found")
    return result
