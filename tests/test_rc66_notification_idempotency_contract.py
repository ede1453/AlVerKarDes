from app.domains.notifications.notification_service import NotificationService


def test_rc66_notification_response_contains_unique_message_ids_per_batch():
    service = NotificationService()

    result = service.deliver(
        {
            "user_id": "rc66-user",
            "channels": ["in_app"],
            "title": "RC66 idempotency",
            "message": "Each message in a batch must have a unique id.",
            "payload": {"source": "rc66"},
        }
    )

    message_ids = [message["notification_id"] for message in result["messages"]]

    assert len(message_ids) == len(set(message_ids))


def test_rc66_notification_batches_get_distinct_batch_ids():
    service = NotificationService()

    payload = {
        "user_id": "rc66-user",
        "channels": ["in_app"],
        "title": "RC66 batch",
        "message": "Batch id must identify one delivery attempt.",
        "payload": {"source": "rc66"},
    }

    first = service.deliver(payload)
    second = service.deliver(payload)

    assert first["batch_id"] != second["batch_id"]


def test_rc66_notification_message_preserves_payload_for_retry_context():
    service = NotificationService()

    result = service.deliver(
        {
            "user_id": "rc66-user",
            "channels": ["in_app"],
            "title": "RC66 retry context",
            "message": "Payload must be available for retry/outbox workers.",
            "payload": {
                "product_key": "macbook-air",
                "alert_id": "rc66-alert",
                "idempotency_key": "rc66-user:macbook-air:rc66-alert",
            },
        }
    )

    message = result["messages"][0]

    assert message["payload"]["product_key"] == "macbook-air"
    assert message["payload"]["alert_id"] == "rc66-alert"
    assert message["payload"]["idempotency_key"] == "rc66-user:macbook-air:rc66-alert"
