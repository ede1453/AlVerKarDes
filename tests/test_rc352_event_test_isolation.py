import pytest

from app.domains.events.event_bus_service import EventBusService
from app.domains.events.event_repository_factory import reset_event_repository


@pytest.fixture(autouse=True)
def clean_event_repository():
    reset_event_repository()


def test_event_repository_can_be_reset_between_tests():
    service = EventBusService()

    service.publish(
        {
            "event_type": "isolation.before_reset",
            "source": "test",
        }
    )

    assert service.status()["event_count"] == 1

    reset_event_repository()

    assert service.status()["event_count"] == 0


def test_new_event_bus_service_starts_from_clean_repository_after_reset():
    reset_event_repository()

    service = EventBusService()
    assert service.status()["event_count"] == 0

    service.publish(
        {
            "event_type": "isolation.after_reset",
            "source": "test",
        }
    )

    assert service.status()["event_count"] == 1
