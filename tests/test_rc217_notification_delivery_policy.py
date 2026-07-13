from app.domains.deal_notifications.provider_governance import DeliveryPolicyEngine


def test_rc217_delivery_allowed():
    result = DeliveryPolicyEngine().evaluate(
        notification={
            "channel":"push",
            "status":"READY",
        },
        user_preferences={
            "enabled_channels":["push"]
        },
        provider_available=True,
        unsubscribe_status=False,
    )
    assert result["allowed"] is True

def test_rc217_delivery_blocked_when_unsubscribed():
    result = DeliveryPolicyEngine().evaluate(
        notification={
            "channel":"email",
            "status":"READY",
        },
        user_preferences={
            "enabled_channels":["email"]
        },
        provider_available=True,
        unsubscribe_status=True,
    )
    assert result["allowed"] is False
    assert "USER_UNSUBSCRIBED" in result["blocking_reasons"]
