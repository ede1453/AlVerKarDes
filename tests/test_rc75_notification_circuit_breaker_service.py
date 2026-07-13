from app.domains.notifications.outbox.outbox_service import NotificationOutboxService


def test_rc75_circuit_breaker_empty_state_is_closed():
    service = NotificationOutboxService()

    result = service.get_circuit_breaker_status()

    assert result["status"] == "CLOSED"
    assert result["failure_count"] == 0
    assert result["metadata"]["circuit_breaker_version"] == "notification_circuit_breaker_v1"


def test_rc75_circuit_breaker_opens_after_dead_letter_threshold():
    service = NotificationOutboxService()

    for index in range(3):
        queued = service.enqueue(
            {
                "user_id": "rc75-user",
                "title": f"RC75 {index}",
                "message": "Circuit breaker",
                "payload": {"source": "rc75"},
            }
        )

        for _ in range(3):
            service.claim_next()
            failed = service.mark_failed(
                item_id=queued["id"],
                error="PROVIDER_TIMEOUT",
                next_retry_at="2000-01-01T00:00:00+00:00",
            )
            if failed["item"]["status"] != "DEAD_LETTER":
                service.requeue_due_retries()

    result = service.get_circuit_breaker_status(failure_threshold=3)

    assert result["status"] == "OPEN"
    assert result["failure_count"] == 3
    assert result["failure_threshold"] == 3


def test_rc75_circuit_breaker_allows_delivery_when_closed():
    service = NotificationOutboxService()

    assert service.can_deliver_notifications()["allowed"] is True


def test_rc75_circuit_breaker_blocks_delivery_when_open():
    service = NotificationOutboxService()

    for index in range(3):
        queued = service.enqueue(
            {
                "user_id": "rc75-user",
                "title": f"RC75 {index}",
                "message": "Circuit breaker block",
                "payload": {"source": "rc75"},
            }
        )

        for _ in range(3):
            service.claim_next()
            failed = service.mark_failed(
                item_id=queued["id"],
                error="PROVIDER_TIMEOUT",
                next_retry_at="2000-01-01T00:00:00+00:00",
            )
            if failed["item"]["status"] != "DEAD_LETTER":
                service.requeue_due_retries()

    result = service.can_deliver_notifications(failure_threshold=3)

    assert result["allowed"] is False
    assert result["reason"] == "CIRCUIT_BREAKER_OPEN"
