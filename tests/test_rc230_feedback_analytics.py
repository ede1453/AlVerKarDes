from app.domains.consumer_trust.service import ConsumerTrustService


def test_rc230_feedback_analytics():
    service = ConsumerTrustService()
    service.record_feedback(
        user_id="u1",
        recommendation_id="r1",
        feedback_type="HELPFUL",
    )
    service.record_feedback(
        user_id="u2",
        recommendation_id="r1",
        feedback_type="NOT_HELPFUL",
    )
    result = service.summarize_feedback(
        recommendation_id="r1"
    )
    assert result["feedback_count"] == 2
    assert result["helpfulness_rate"] == 0.5
