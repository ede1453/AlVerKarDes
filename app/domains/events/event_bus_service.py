from app.domains.events.event_models import EventCreate, create_event_record
from app.domains.events.event_repository import InMemoryEventRepository
from app.domains.events.event_repository_factory import get_event_repository
from app.domains.events.event_serializer import serialize_event


class EventBusService:
    def __init__(self, repository: InMemoryEventRepository | None = None):
        self.repository = repository or get_event_repository()

    def publish(self, payload: dict):
        event = create_event_record(
            EventCreate(
                event_type=payload["event_type"],
                source=payload.get("source", "system"),
                payload=payload.get("payload", {}),
                metadata=payload.get("metadata", {}),
            )
        )
        return serialize_event(self.repository.publish(event))

    def list_recent(self, payload: dict | None = None):
        payload = payload or {}
        return [
            serialize_event(event)
            for event in self.repository.list_recent(
                limit=payload.get("limit", 50),
                event_type=payload.get("event_type"),
                source=payload.get("source"),
            )
        ]

    def status(self):
        return {
            "enabled": True,
            "backend": "memory",
            "event_count": self.repository.count(),
            "event_bus_version": "event_bus_v1",
            "repository_lifecycle": "singleton",
        }

    def clear(self):
        self.repository.clear()
        return self.status()
