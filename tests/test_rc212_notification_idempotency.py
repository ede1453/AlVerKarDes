from app.domains.deal_notifications.operations import DealNotificationOperationsService


def test_rc212_duplicate_notification_blocked():
    service = DealNotificationOperationsService()

    first = service.reserve_idempotency_key(
        user_id="u1",
        deal_id="d1",
        channel="push",
        window_key="2026-07-12",
    )

    second = service.reserve_idempotency_key(
        user_id="u1",
        deal_id="d1",
        channel="push",
        window_key="2026-07-12",
    )

    assert first["reserved"] is True
    assert second["reserved"] is False
    assert second["reason"] == "DUPLICATE_NOTIFICATION"
    assert second["notification_id"] == first["notification_id"]
