from app.domains.notifications.outbox.outbox_service import (
    NotificationOutboxService,
)


async def test_rc74_channel_health_empty():
    service = NotificationOutboxService()

    result = await service.get_channel_health()

    assert result["channels"] == []
    assert (
        result["metadata"]["channel_health_version"]
        == "notification_channel_health_v1"
    )
