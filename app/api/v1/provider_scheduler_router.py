from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.internal_service_auth import require_internal_service_key
from app.domains.provider_scheduler.provider_scheduler_repository import (
    ProviderSchedulerDBRepository,
)
from app.domains.provider_scheduler.provider_scheduler_service import (
    DEFAULT_STALE_LOCK_SECONDS,
    ProviderSchedulerService,
)


class ProviderScheduleCreateRequest(BaseModel):
    name: str
    providers: list[str] = Field(default_factory=lambda: ["mock", "openai", "local"])
    interval_seconds: int = Field(default=60, ge=1, le=86400)
    enabled: bool = True


class ProviderScheduleClaimRequest(BaseModel):
    worker_id: str
    stale_lock_seconds: int = DEFAULT_STALE_LOCK_SECONDS
    # None = pick the next enabled, due schedule; set = lock this one
    # specific schedule (used by a due-schedule poller vs. a targeted claim).
    schedule_id: str | None = None


class ProviderScheduleCompleteRequest(BaseModel):
    result: dict = Field(default_factory=dict)


router = APIRouter(prefix="/provider-schedules", tags=["provider-schedules"])


def _service(db: AsyncSession) -> ProviderSchedulerService:
    # SCALE-004: Postgres-backed now (ProviderSchedulerDBRepository) --
    # same per-request construction pattern as JobDBRepository
    # (job_queue_router.py, SCALE-003). No more module-level singleton: a
    # shared instance can't hold a request-scoped AsyncSession, and
    # claim()'s SELECT FOR UPDATE SKIP LOCKED needs a real transaction per
    # request anyway.
    return ProviderSchedulerService(repository=ProviderSchedulerDBRepository(db))


@router.post("")
async def create_provider_schedule(
    payload: ProviderScheduleCreateRequest,
    db: AsyncSession = Depends(get_db),
    # AUTH-004 (ADR-006): servis-arası çağrı, X-Internal-Service-Key gerektirir.
    internal_service=Depends(require_internal_service_key),
):
    return await _service(db).create(payload.model_dump())


@router.get("")
async def list_provider_schedules(
    db: AsyncSession = Depends(get_db),
    # AUTH-004 (ADR-006): servis-arası çağrı, X-Internal-Service-Key gerektirir.
    internal_service=Depends(require_internal_service_key),
):
    return {"items": await _service(db).list()}


@router.get("/{schedule_id}")
async def get_provider_schedule(
    schedule_id: str,
    db: AsyncSession = Depends(get_db),
    # AUTH-004 (ADR-006): servis-arası çağrı, X-Internal-Service-Key gerektirir.
    internal_service=Depends(require_internal_service_key),
):
    result = await _service(db).get(schedule_id)
    if result is None:
        raise HTTPException(status_code=404, detail="provider_schedule_not_found")
    return result


@router.post("/claim-next")
async def claim_next_provider_schedule(
    payload: ProviderScheduleClaimRequest,
    db: AsyncSession = Depends(get_db),
    # AUTH-004 (ADR-006): servis-arası çağrı, X-Internal-Service-Key gerektirir.
    internal_service=Depends(require_internal_service_key),
):
    schedule = await _service(db).claim_next(
        worker_id=payload.worker_id,
        stale_lock_seconds=payload.stale_lock_seconds,
        schedule_id=payload.schedule_id,
    )
    return {"schedule": schedule}


@router.post("/{schedule_id}/complete")
async def complete_provider_schedule(
    schedule_id: str,
    payload: ProviderScheduleCompleteRequest,
    db: AsyncSession = Depends(get_db),
    # AUTH-004 (ADR-006): servis-arası çağrı, X-Internal-Service-Key gerektirir.
    internal_service=Depends(require_internal_service_key),
):
    result = await _service(db).complete(schedule_id, payload.result)
    if result is None:
        raise HTTPException(status_code=404, detail="provider_schedule_not_found")
    return result


@router.post("/{schedule_id}/run-once")
async def run_provider_schedule_once(
    schedule_id: str,
    db: AsyncSession = Depends(get_db),
    # AUTH-004 (ADR-006): servis-arası çağrı, X-Internal-Service-Key gerektirir.
    internal_service=Depends(require_internal_service_key),
):
    result = await _service(db).run_once(schedule_id)
    if result is None:
        raise HTTPException(status_code=404, detail="provider_schedule_not_found")
    return result


@router.post("/clear")
async def clear_provider_schedules(
    db: AsyncSession = Depends(get_db),
    # AUTH-004 (ADR-006): servis-arası çağrı, X-Internal-Service-Key gerektirir.
    internal_service=Depends(require_internal_service_key),
):
    return await _service(db).clear()
