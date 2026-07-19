from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.core.internal_service_auth import require_internal_service_key
from app.domains.provider_scheduler.provider_scheduler_service import (
    ProviderSchedulerService,
)


class ProviderScheduleCreateRequest(BaseModel):
    name: str
    providers: list[str] = Field(default_factory=lambda: ["mock", "openai", "local"])
    interval_seconds: int = Field(default=60, ge=1, le=86400)
    enabled: bool = True


router = APIRouter(prefix="/provider-schedules", tags=["provider-schedules"])

_service = ProviderSchedulerService()


@router.post("")
async def create_provider_schedule(
    payload: ProviderScheduleCreateRequest,
    # AUTH-004 (ADR-006): servis-arası çağrı, X-Internal-Service-Key gerektirir.
    internal_service=Depends(require_internal_service_key),
):
    return _service.create(payload.model_dump())


@router.get("")
async def list_provider_schedules(
    # AUTH-004 (ADR-006): servis-arası çağrı, X-Internal-Service-Key gerektirir.
    internal_service=Depends(require_internal_service_key),
):
    return {"items": _service.list()}


@router.get("/{schedule_id}")
async def get_provider_schedule(
    schedule_id: str,
    # AUTH-004 (ADR-006): servis-arası çağrı, X-Internal-Service-Key gerektirir.
    internal_service=Depends(require_internal_service_key),
):
    result = _service.get(schedule_id)
    if result is None:
        raise HTTPException(status_code=404, detail="provider_schedule_not_found")
    return result


@router.post("/{schedule_id}/run-once")
async def run_provider_schedule_once(
    schedule_id: str,
    # AUTH-004 (ADR-006): servis-arası çağrı, X-Internal-Service-Key gerektirir.
    internal_service=Depends(require_internal_service_key),
):
    result = _service.run_once(schedule_id)
    if result is None:
        raise HTTPException(status_code=404, detail="provider_schedule_not_found")
    return result


@router.post("/clear")
async def clear_provider_schedules(
    # AUTH-004 (ADR-006): servis-arası çağrı, X-Internal-Service-Key gerektirir.
    internal_service=Depends(require_internal_service_key),
):
    return _service.clear()
