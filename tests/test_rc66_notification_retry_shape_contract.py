from app.domains.notifications.notification_service import NotificationService


def test_rc66_notification_provider_response_has_retry_relevant_shape():
    service = NotificationService()

    result = service.deliver(
        {
            "user_id": "rc66-user",
            "channels": ["in_app"],
            "title": "RC66 provider response",
            "message": "Provider response should expose retry-relevant status.",
            "payload": {"source": "rc66"},
        }
    )

    message = result["messages"][0]
    provider_response = message["provider_response"]

    assert "status" in provider_response
    assert "provider" in provider_response
    assert provider_response["status"] in {"DELIVERED", "FAILED", "QUEUED"}


def test_rc66_notification_message_has_retry_relevant_core_fields():
    service = NotificationService()

    result = service.deliver(
        {
            "user_id": "rc66-user",
            "channels": ["in_app"],
            "title": "RC66 retry fields",
            "message": "Message shape must support future retry/outbox persistence.",
            "payload": {"source": "rc66"},
        }
    )

    message = result["messages"][0]

    assert "notification_id" in message
    assert "user_id" in message
    assert "channel" in message
    assert "title" in message
    assert "message" in message
    assert "payload" in message
    assert "status" in message
    assert "provider" in message
    assert "created_at" in message
