from app.domains.notifications.outbox.outbox_service import NotificationOutboxService


def test_rc68_claim_next_returns_no_item_when_empty():
    service = NotificationOutboxService()

    result = service.claim_next()

    assert result["claimed"] is False
    assert result["item"] is None


def test_rc68_claim_next_marks_pending_item_processing():
    service = NotificationOutboxService()
    queued = service.enqueue(
        {
            "user_id": "rc68-user",
            "title": "RC68",
            "message": "Worker claim",
            "payload": {"source": "rc68"},
        }
    )

    result = service.claim_next()

    assert result["claimed"] is True
    assert result["item"]["id"] == queued["id"]
    assert result["item"]["status"] == "PROCESSING"


def test_rc68_mark_delivered_updates_claimed_item():
    service = NotificationOutboxService()
    service.enqueue({"user_id": "rc68-user", "title": "RC68", "message": "Delivered"})
    claimed = service.claim_next()

    result = service.mark_delivered(claimed["item"]["id"])

    assert result["updated"] is True
    assert result["item"]["status"] == "DELIVERED"
    assert result["item"]["last_error"] is None


def test_rc68_mark_failed_updates_retry_count():
    service = NotificationOutboxService()
    service.enqueue({"user_id": "rc68-user", "title": "RC68", "message": "Failed"})
    claimed = service.claim_next()

    result = service.mark_failed(claimed["item"]["id"], error="PROVIDER_TIMEOUT")

    assert result["updated"] is True
    assert result["item"]["status"] == "FAILED"
    assert result["item"]["retry_count"] == 1
    assert result["item"]["last_error"] == "PROVIDER_TIMEOUT"


def test_rc68_mark_missing_item_returns_not_found():
    service = NotificationOutboxService()

    result = service.mark_delivered("missing-id")

    assert result["updated"] is False
    assert result["error"] == "NOT_FOUND"
