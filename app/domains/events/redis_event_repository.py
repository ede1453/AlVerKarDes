import json
from datetime import datetime

from app.domains.cache.cache_namespace import build_namespaced_cache_key
from app.domains.events.event_models import EventRecord


class RedisEventRepository:
    """SCALE-006: Redis-backed event log. Mirrors RedisRateLimitStore's
    factory wiring (SCALE-001) -- same AICI_REDIS_URL, same namespace
    convention via build_namespaced_cache_key, no new dependency/config
    surface.

    Fixes the same class of defect as SCALE-001..004: InMemoryEventRepository's
    list was per-process, so an event published on one worker was invisible
    to every other worker/process reading the event log (event_bus_router's
    GET /events, GET /events/status, and the 20+ domain services that publish
    through EventBusService). RPUSH is atomic in Redis, so concurrent
    publishes from different worker processes append to the SAME ordered
    list -- no lost writes, no duplicate entries.
    """

    backend = "redis"
    _LIST_KEY = "events:log"

    def __init__(self, redis_client):
        self.redis_client = redis_client

    def _key(self) -> str:
        return build_namespaced_cache_key(self._LIST_KEY)

    def publish(self, event: EventRecord) -> EventRecord:
        self.redis_client.rpush(self._key(), _serialize(event))
        return event

    def list_recent(self, *, limit: int = 50, event_type: str | None = None, source: str | None = None):
        raw_events = self.redis_client.lrange(self._key(), 0, -1)
        events = [_deserialize(raw) for raw in reversed(raw_events)]

        if event_type:
            events = [event for event in events if event.event_type == event_type]

        if source:
            events = [event for event in events if event.source == source]

        return events[:limit]

    def clear(self):
        self.redis_client.delete(self._key())

    def count(self) -> int:
        return self.redis_client.llen(self._key())


def _serialize(event: EventRecord) -> str:
    return json.dumps(
        {
            "id": event.id,
            "event_type": event.event_type,
            "source": event.source,
            "payload": event.payload,
            "metadata": event.metadata,
            "status": event.status,
            "created_at": event.created_at.isoformat(),
        }
    )


def _deserialize(raw) -> EventRecord:
    data = json.loads(raw)
    return EventRecord(
        id=data["id"],
        event_type=data["event_type"],
        source=data["source"],
        payload=data["payload"],
        metadata=data["metadata"],
        status=data["status"],
        created_at=datetime.fromisoformat(data["created_at"]),
    )
