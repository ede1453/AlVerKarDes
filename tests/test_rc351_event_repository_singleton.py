from app.domains.events.event_bus_service import EventBusService
from app.domains.events.event_repository_factory import (
    get_event_repository,
    reset_event_repository,
)


def test_event_repository_factory_returns_singleton_instance():
    first = get_event_repository()
    second = get_event_repository()

    assert first is second


def test_event_bus_services_share_singleton_repository_by_default():
    reset_event_repository()

    publisher = EventBusService()
    reader = EventBusService()

    event = publisher.publish(
        {
            "event_type": "singleton.test",
            "source": "test",
            "payload": {"ok": True},
        }
    )

    events = reader.list_recent(
        {
            "event_type": "singleton.test",
            "source": "test",
        }
    )

    assert events
    assert events[0]["id"] == event["id"]
