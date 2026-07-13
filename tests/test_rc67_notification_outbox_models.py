
from app.domains.notifications.outbox.outbox_models import (
    DEAD_LETTER,
    DELIVERED,
    FAILED,
    PENDING,
    PROCESSING,
    NotificationOutboxItem,
)


def test_rc67_notification_outbox_item_defaults_to_pending():
    item = NotificationOutboxItem(user_id="user-1", title="Title", message="Message")

    assert item.status == PENDING
    assert item.retry_count == 0
    assert item.max_retries == 3
    assert item.channel == "in_app"


def test_rc67_notification_outbox_item_status_transitions():
    item = NotificationOutboxItem(user_id="user-1", title="Title", message="Message")

    item.mark_processing()
    assert item.status == PROCESSING

    item.mark_delivered()
    assert item.status == DELIVERED
    assert item.last_error is None


def test_rc67_notification_outbox_item_failure_transitions_to_dead_letter_after_max_retries():
    item = NotificationOutboxItem(user_id="user-1", title="Title", message="Message", max_retries=2)

    item.mark_failed("first")
    assert item.status == FAILED
    assert item.retry_count == 1

    item.mark_failed("second")
    assert item.status == DEAD_LETTER
    assert item.retry_count == 2


def test_rc67_notification_outbox_item_to_dict_is_json_ready():
    item = NotificationOutboxItem(
        user_id="user-1",
        title="Title",
        message="Message",
        payload={"product_key": "macbook-air"},
    )

    data = item.to_dict()

    assert data["user_id"] == "user-1"
    assert data["payload"]["product_key"] == "macbook-air"
    assert isinstance(data["created_at"], str)
