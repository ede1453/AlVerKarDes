from app.domains.notifications.outbox.outbox_service import NotificationOutboxService


def test_rc73_metrics_empty_outbox():
    service = NotificationOutboxService()

    metrics = service.get_metrics()

    assert metrics["total_count"] == 0
    assert metrics["pending_count"] == 0
    assert metrics["processing_count"] == 0
    assert metrics["delivered_count"] == 0
    assert metrics["failed_count"] == 0
    assert metrics["dead_letter_count"] == 0
    assert metrics["delivery_success_rate"] == 0.0
    assert metrics["metadata"]["metrics_version"] == "notification_metrics_v1"


def test_rc73_metrics_counts_statuses():
    service = NotificationOutboxService()

    pending = service.enqueue({"user_id": "u1", "title": "P", "message": "Pending"})
    delivered = service.enqueue({"user_id": "u1", "title": "D", "message": "Delivered"})
    service.enqueue({"user_id": "u1", "title": "F", "message": "Failed"})

    service.claim_next()
    service.mark_delivered(pending["id"])

    service.claim_next()
    service.mark_failed(
        item_id=delivered["id"],
        error="PROVIDER_TIMEOUT",
        next_retry_at="2000-01-01T00:00:00+00:00",
    )

    metrics = service.get_metrics()

    assert metrics["total_count"] == 3
    assert metrics["delivered_count"] == 1
    assert metrics["failed_count"] == 1
    assert metrics["pending_count"] == 1


def test_rc73_metrics_counts_dead_letters():
    service = NotificationOutboxService()
    queued = service.enqueue({"user_id": "u1", "title": "DLQ", "message": "Dead"})

    for _ in range(3):
        service.claim_next()
        failed = service.mark_failed(
            item_id=queued["id"],
            error="PROVIDER_TIMEOUT",
            next_retry_at="2000-01-01T00:00:00+00:00",
        )
        if failed["item"]["status"] != "DEAD_LETTER":
            service.requeue_due_retries()

    metrics = service.get_metrics()

    assert metrics["dead_letter_count"] == 1
    assert metrics["failed_count"] == 0
    assert metrics["retry_count_total"] == 3

