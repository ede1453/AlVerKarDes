from app.domains.deal_notifications.provider_governance import NotificationProviderRegistry


def test_rc216_provider_priority_selection():
    registry = NotificationProviderRegistry()

    registry.register_provider(
        provider_id="push-b",
        channel="push",
        priority=20,
    )
    registry.register_provider(
        provider_id="push-a",
        channel="push",
        priority=10,
    )

    result = registry.select_provider(
        channel="push"
    )

    assert result["selected"] is True
    assert result["provider"]["provider_id"] == "push-a"
