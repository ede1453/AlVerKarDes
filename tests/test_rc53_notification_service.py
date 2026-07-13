from app.domains.events.event_repository_factory import reset_event_repository
from app.domains.notifications.notification_service import NotificationService


def test_notification_service_delivers_mock_in_app_and_emits_event():
    reset_event_repository()
    service = NotificationService()

    result = service.deliver(
        {
            "user_id": "user-1",
            "channels": ["in_app"],
            "title": "Strong deal detected",
            "message": "MacBook Air has strong buy signals.",
            "payload": {"product_key": "macbook-air"},
        }
    )

    assert result["delivered_count"] == 1
    assert result["messages"][0]["status"] == "DELIVERED"

    events = service.event_bus_service.list_recent(
        {"event_type": "notification.delivery_completed", "source": "notifications"}
    )
    assert events


def test_notification_service_external_provider_boundary():
    service = NotificationService()

    result = service.deliver(
        {
            "user_id": "user-1",
            "channels": ["email"],
            "title": "Strong deal detected",
            "message": "MacBook Air has strong buy signals.",
            "provider": "external",
        }
    )

    assert result["delivered_count"] == 0
    assert result["messages"][0]["status"] == "PROVIDER_NOT_CONFIGURED"


def test_notification_service_from_smart_alert():
    service = NotificationService()

    result = service.deliver_from_smart_alert(
        {
            "user_id": "user-1",
            "smart_alert": {
                "title": "Strong deal detected",
                "message": "This product currently has strong buy signals.",
                "channels": ["in_app"],
            },
        }
    )

    assert result["delivered_count"] == 1
