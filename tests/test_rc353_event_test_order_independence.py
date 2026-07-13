from app.domains.events.event_bus_service import EventBusService
from app.domains.events.event_repository_factory import reset_event_repository


def test_event_repository_reset_makes_test_order_independent():
    reset_event_repository()

    first_service = EventBusService()
    first_service.publish(
        {
            "event_type": "order.first",
            "source": "test",
        }
    )
    assert first_service.status()["event_count"] == 1

    reset_event_repository()

    second_service = EventBusService()
    second_service.publish(
        {
            "event_type": "order.second",
            "source": "test",
        }
    )

    events = second_service.list_recent({"limit": 10})

    assert second_service.status()["event_count"] == 1
    assert len(events) == 1
    assert events[0]["event_type"] == "order.second"
