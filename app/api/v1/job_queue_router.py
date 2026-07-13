from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.domains.jobs.job_queue_service import JobQueueService


class JobCreateRequest(BaseModel):
    job_type: str
    payload: dict = Field(default_factory=dict)


router = APIRouter(prefix="/jobs", tags=["jobs"])

_service = JobQueueService()


@router.post("/enqueue")
async def enqueue_job(payload: JobCreateRequest):
    return _service.enqueue(payload.model_dump())


@router.post("/run-now")
async def run_job_now(payload: JobCreateRequest):
    return _service.run_now(payload.model_dump())


@router.get("")
async def list_jobs(limit: int = Query(default=20, ge=1, le=100)):
    return {
        "items": _service.list_recent(limit=limit),
        "limit": limit,
    }


@router.get("/{job_id}")
async def get_job(job_id: str):
    result = _service.get(job_id)
    if result is None:
        raise HTTPException(status_code=404, detail="job_not_found")
    return result
