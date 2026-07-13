from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

from app.domains.events.event_bus_service import EventBusService
from app.domains.events.event_repository_factory import get_event_repository


class EventPublishRequest(BaseModel):
    event_type: str
    source: str = "system"
    payload: dict = Field(default_factory=dict)
    metadata: dict = Field(default_factory=dict)


router = APIRouter(prefix="/events", tags=["events"])

_service = EventBusService(repository=get_event_repository())


@router.post("/publish")
async def publish_event(payload: EventPublishRequest):
    return _service.publish(payload.model_dump())


@router.get("")
async def list_events(
    limit: int = Query(default=50, ge=1, le=200),
    event_type: str | None = None,
    source: str | None = None,
):
    return {
        "items": _service.list_recent(
            {
                "limit": limit,
                "event_type": event_type,
                "source": source,
            }
        ),
        "limit": limit,
    }


@router.get("/status")
async def event_bus_status():
    return _service.status()


@router.post("/clear")
async def clear_events():
    return _service.clear()
