from app.domains.events.event_models import EventRecord


class InMemoryEventRepository:
    backend = "memory"

    def __init__(self):
        self._events: list[EventRecord] = []

    def publish(self, event: EventRecord) -> EventRecord:
        self._events.append(event)
        return event

    def list_recent(self, *, limit: int = 50, event_type: str | None = None, source: str | None = None):
        events = list(reversed(self._events))

        if event_type:
            events = [event for event in events if event.event_type == event_type]

        if source:
            events = [event for event in events if event.source == source]

        return events[:limit]

    def clear(self):
        self._events.clear()

    def count(self) -> int:
        return len(self._events)
