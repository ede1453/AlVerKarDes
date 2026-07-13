from datetime import datetime, timedelta, timezone

from app.domains.notifications.outbox.outbox_service import NotificationOutboxService


def test_rc69_failed_item_can_be_scheduled_for_retry():
    service = NotificationOutboxService()
    queued = service.enqueue(
        {
            "user_id": "rc69-user",
            "title": "RC69",
            "message": "Retry scheduling",
            "payload": {"source": "rc69"},
        }
    )

    service.claim_next()
    next_retry_at = (datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat()
    failed = service.mark_failed(
        item_id=queued["id"],
        error="PROVIDER_TIMEOUT",
        next_retry_at=next_retry_at,
    )

    assert failed["updated"] is True
    assert failed["item"]["status"] == "FAILED"
    assert failed["item"]["next_retry_at"] == next_retry_at


def test_rc69_requeue_due_retries_moves_failed_item_back_to_pending():
    service = NotificationOutboxService()
    queued = service.enqueue(
        {
            "user_id": "rc69-user",
            "title": "RC69",
            "message": "Due retry",
            "payload": {"source": "rc69"},
        }
    )

    service.claim_next()
    next_retry_at = (datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat()
    service.mark_failed(
        item_id=queued["id"],
        error="PROVIDER_TIMEOUT",
        next_retry_at=next_retry_at,
    )

    result = service.requeue_due_retries()

    assert result["requeued_count"] == 1
    assert result["items"][0]["id"] == queued["id"]
    assert result["items"][0]["status"] == "PENDING"

    pending = service.list_pending()
    assert pending["pending_count"] == 1
    assert pending["items"][0]["id"] == queued["id"]


def test_rc69_requeue_due_retries_does_not_requeue_future_items():
    service = NotificationOutboxService()
    queued = service.enqueue(
        {
            "user_id": "rc69-user",
            "title": "RC69",
            "message": "Future retry",
            "payload": {"source": "rc69"},
        }
    )

    service.claim_next()
    next_retry_at = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
    service.mark_failed(
        item_id=queued["id"],
        error="PROVIDER_TIMEOUT",
        next_retry_at=next_retry_at,
    )

    result = service.requeue_due_retries()

    assert result["requeued_count"] == 0
    assert result["items"] == []


def test_rc69_dead_letter_item_is_not_requeued():
    service = NotificationOutboxService()
    queued = service.enqueue(
        {
            "user_id": "rc69-user",
            "title": "RC69",
            "message": "Dead letter",
            "payload": {"source": "rc69"},
        }
    )

    for _ in range(3):
        service.claim_next()
        service.mark_failed(
            item_id=queued["id"],
            error="PROVIDER_TIMEOUT",
            next_retry_at=(datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat(),
        )
        service.requeue_due_retries()

    result = service.requeue_due_retries()

    assert result["requeued_count"] == 0
