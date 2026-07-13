from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4


@dataclass
class EventCreate:
    event_type: str
    source: str
    payload: dict = field(default_factory=dict)
    metadata: dict = field(default_factory=dict)


@dataclass
class EventRecord:
    id: str
    event_type: str
    source: str
    payload: dict
    metadata: dict
    status: str
    created_at: datetime


def create_event_record(data: EventCreate) -> EventRecord:
    return EventRecord(
        id=str(uuid4()),
        event_type=data.event_type,
        source=data.source,
        payload=dict(data.payload),
        metadata=dict(data.metadata),
        status="PUBLISHED",
        created_at=datetime.now(timezone.utc),
    )
