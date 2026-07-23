import pytest

from app.domains.deal_notifications.idempotency_store_factory import (
    reset_memory_idempotency_store,
)
from app.domains.deal_notifications.operations import DealNotificationOperationsService


@pytest.fixture(autouse=True)
def clean_idempotency_store():
    # SCALE-007 Part 2: the default in-memory store is now a shared
    # singleton (env-driven factory, same identity as
    # get_event_repository()/get_rate_limit_store() in memory mode) rather
    # than a fresh dict per DealNotificationOperationsService() instance --
    # reset before each test, same discipline as
    # test_rc35_event_bus_service.py's clean_event_repository fixture.
    reset_memory_idempotency_store()


def test_rc212_duplicate_notification_blocked():
    service = DealNotificationOperationsService()

    first = service.reserve_idempotency_key(
        user_id="u1",
        deal_id="d1",
        channel="push",
        window_key="2026-07-12",
    )

    second = service.reserve_idempotency_key(
        user_id="u1",
        deal_id="d1",
        channel="push",
        window_key="2026-07-12",
    )

    assert first["reserved"] is True
    assert second["reserved"] is False
    assert second["reason"] == "DUPLICATE_NOTIFICATION"
    assert second["notification_id"] == first["notification_id"]
