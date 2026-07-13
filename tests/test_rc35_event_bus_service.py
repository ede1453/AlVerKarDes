import pytest

from app.domains.events.event_bus_service import EventBusService
from app.domains.events.event_repository_factory import reset_event_repository


@pytest.fixture(autouse=True)
def clean_event_repository():
    reset_event_repository()


def test_event_bus_service_publish_and_status():
    service = EventBusService()

    event = service.publish(
        {
            "event_type": "orchestration.completed",
            "source": "llm_orchestration",
            "payload": {"status": "COMPLETED"},
        }
    )

    assert event["event_type"] == "orchestration.completed"
    assert service.status()["event_count"] == 1


def test_event_bus_service_list_recent():
    service = EventBusService()
    service.publish({"event_type": "cache.hit", "source": "cache"})
    service.publish({"event_type": "cache.miss", "source": "cache"})

    events = service.list_recent({"limit": 10, "source": "cache"})

    assert len(events) == 2
    assert events[0]["event_type"] == "cache.miss"
