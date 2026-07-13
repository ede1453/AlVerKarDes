from app.domains.consumer_trust.service import ConsumerTrustService


def test_rc227_acceptance_metrics():
    result = ConsumerTrustService().calculate_acceptance_metrics(
        recommendation_count=100,
        viewed_count=50,
        accepted_count=10,
    )
    assert result["view_rate"] == 0.5
    assert result["acceptance_rate"] == 0.2
