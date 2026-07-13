from app.domains.consumer_trust.service import ConsumerTrustService


def test_rc225_delivery_sla():
    result = ConsumerTrustService().evaluate_delivery_sla(
        created_at="2026-07-12T10:00:00+00:00",
        delivered_at="2026-07-12T10:00:20+00:00",
        target_seconds=30,
    )
    assert result["met"] is True
