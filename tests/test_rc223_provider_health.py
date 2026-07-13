from app.domains.consumer_trust.service import ConsumerTrustService


def test_rc223_provider_health():
    result = ConsumerTrustService().calculate_provider_health(
        provider_id="p1",
        success_count=99,
        failure_count=1,
        average_latency_ms=100,
    )
    assert result["status"] == "HEALTHY"
