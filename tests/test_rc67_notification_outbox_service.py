from app.domains.notifications.outbox.outbox_service import NotificationOutboxService


def test_rc67_outbox_service_enqueue_single_notification():
    service = NotificationOutboxService()

    result = service.enqueue(
        {
            "user_id": "user-1",
            "channel": "in_app",
            "title": "Title",
            "message": "Message",
            "payload": {"idempotency_key": "user-1:title"},
        }
    )

    assert result["user_id"] == "user-1"
    assert result["status"] == "PENDING"
    assert result["idempotency_key"] == "user-1:title"


def test_rc67_outbox_service_enqueue_many_notifications():
    service = NotificationOutboxService()

    result = service.enqueue_many(
        [
            {"user_id": "user-1", "title": "One", "message": "Message"},
            {"user_id": "user-2", "title": "Two", "message": "Message"},
        ]
    )

    assert result["queued_count"] == 2
    assert result["metadata"]["outbox_version"] == "notification_outbox_v1"


def test_rc67_outbox_service_list_pending():
    service = NotificationOutboxService()
    service.enqueue({"user_id": "user-1", "title": "One", "message": "Message"})

    result = service.list_pending()

    assert result["pending_count"] == 1
    assert result["items"][0]["status"] == "PENDING"
