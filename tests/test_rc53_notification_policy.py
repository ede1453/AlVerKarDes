from app.domains.notifications.notification_policy import NotificationPolicy


def test_notification_policy_allows_in_app():
    result = NotificationPolicy().evaluate(
        user_id="user-1",
        channel="in_app",
        title="Deal",
        message="Strong deal detected",
    )

    assert result["allowed"] is True


def test_notification_policy_blocks_unsupported_channel():
    result = NotificationPolicy().evaluate(
        user_id="user-1",
        channel="sms",
        title="Deal",
        message="Strong deal detected",
    )

    assert result["allowed"] is False
    assert result["reason"] == "UNSUPPORTED_CHANNEL"
