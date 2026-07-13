from app.domains.consumer_trust.service import ConsumerTrustService


def test_rc229_source_trust_adjustment():
    result = ConsumerTrustService().adjust_source_trust(
        source_id="amazon",
        current_score=80,
        verified_successes=10,
        false_positive_count=1,
        complaint_count=1,
    )
    assert result["trust_score"] == 78.0
