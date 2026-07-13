from app.domains.consumer_trust.service import ConsumerTrustService


def test_rc222_frequency_cap():
    service = ConsumerTrustService()
    for _ in range(3):
        service.record_delivery(
            user_id="u1",
            channel="push",
            delivered_at="2026-07-12T10:00:00+00:00",
        )
    result = service.evaluate_frequency_cap(
        user_id="u1",
        channel="push",
        max_deliveries=3,
        window_hours=24,
        reference_time="2026-07-12T12:00:00+00:00",
    )
    assert result["allowed"] is False
