from app.domains.consumer_trust.service import ConsumerTrustService


def test_rc221_notification_fatigue():
    result = ConsumerTrustService().calculate_notification_fatigue(
        delivered_count_24h=10,
        opened_count_24h=1,
        dismissed_count_24h=4,
        duplicate_count_24h=2,
    )
    assert result["fatigue_level"] == "HIGH"
