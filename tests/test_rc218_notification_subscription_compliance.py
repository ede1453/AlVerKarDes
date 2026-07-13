from app.domains.deal_notifications.provider_governance import SubscriptionComplianceService


def test_rc218_unsubscribe_state():
    service = SubscriptionComplianceService()

    service.set_subscription(
        user_id="u1",
        channel="email",
        subscribed=False,
        source="user_request",
    )

    assert service.is_unsubscribed(
        user_id="u1",
        channel="email",
    ) is True
