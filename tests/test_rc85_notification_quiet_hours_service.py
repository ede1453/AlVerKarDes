from app.domains.notifications.outbox.outbox_service import NotificationOutboxService


def test_rc85_quiet_hours_disabled_allows_delivery():
    service = NotificationOutboxService()

    result = service.check_quiet_hours(
        user_id="rc85-user",
        current_hour=23,
        enabled=False,
    )

    assert result["allowed"] is True
    assert result["quiet_hours_active"] is False
    assert result["reason"] == "QUIET_HOURS_DISABLED"


def test_rc85_quiet_hours_blocks_inside_overnight_window():
    service = NotificationOutboxService()

    result = service.check_quiet_hours(
        user_id="rc85-user",
        current_hour=23,
        start_hour=22,
        end_hour=8,
        enabled=True,
    )

    assert result["allowed"] is False
    assert result["quiet_hours_active"] is True
    assert result["reason"] == "QUIET_HOURS_ACTIVE"


def test_rc85_quiet_hours_allows_outside_overnight_window():
    service = NotificationOutboxService()

    result = service.check_quiet_hours(
        user_id="rc85-user",
        current_hour=14,
        start_hour=22,
        end_hour=8,
        enabled=True,
    )

    assert result["allowed"] is True
    assert result["quiet_hours_active"] is False
    assert result["reason"] == "OUTSIDE_QUIET_HOURS"


def test_rc85_quiet_hours_supports_same_day_window():
    service = NotificationOutboxService()

    blocked = service.check_quiet_hours(
        user_id="rc85-user",
        current_hour=13,
        start_hour=12,
        end_hour=15,
        enabled=True,
    )
    allowed = service.check_quiet_hours(
        user_id="rc85-user",
        current_hour=16,
        start_hour=12,
        end_hour=15,
        enabled=True,
    )

    assert blocked["allowed"] is False
    assert allowed["allowed"] is True
