from app.domains.notifications.notification_service import NotificationService


def test_rc65_notification_service_returns_batch_metadata():
    service = NotificationService()

    result = service.deliver(
        {
            "user_id": "rc65-user",
            "channels": ["in_app"],
            "title": "RC65",
            "message": "Queue semantics check.",
            "payload": {"source": "rc65"},
        }
    )

    assert "batch_id" in result
    assert result["user_id"] == "rc65-user"
    assert result["requested_channels"] == ["in_app"]
    assert result["delivered_count"] + result["failed_count"] == len(result["messages"])
    assert result["metadata"]["notification_version"] == "notification_boundary_v1"


def test_rc65_notification_service_keeps_payload_attached_to_message():
    service = NotificationService()

    result = service.deliver(
        {
            "user_id": "rc65-user",
            "channels": ["in_app"],
            "title": "RC65 payload",
            "message": "Payload must survive delivery boundary.",
            "payload": {"product_key": "macbook-air", "source": "rc65"},
        }
    )

    message = result["messages"][0]

    assert message["payload"]["product_key"] == "macbook-air"
    assert message["payload"]["source"] == "rc65"
