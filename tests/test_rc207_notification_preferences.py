from app.domains.deal_notifications.service import NotificationPreferenceService


def test_rc207_store_preferences():
    service = NotificationPreferenceService()
    result = service.set_preferences(
        user_id="user-1",
        enabled_channels=["push","email","push"],
        minimum_confidence=80,
        minimum_discount_pct=20,
        quiet_hours_enabled=True,
    )
    assert result["updated"] is True
    assert result["preferences"]["enabled_channels"] == ["email","push"]
    assert service.get_preferences(
        "user-1"
    )["minimum_confidence"] == 80
