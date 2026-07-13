from app.domains.consumer_trust.service import ConsumerTrustService


def test_rc224_provider_fallback():
    service = ConsumerTrustService()
    service.calculate_provider_health(
        provider_id="p1",
        success_count=50,
        failure_count=50,
        average_latency_ms=100,
    )
    service.calculate_provider_health(
        provider_id="p2",
        success_count=99,
        failure_count=1,
        average_latency_ms=100,
    )
    result = service.select_provider_fallback(
        provider_ids=["p1","p2"],
        minimum_health_score=70,
    )
    assert result["provider"]["provider_id"] == "p2"
