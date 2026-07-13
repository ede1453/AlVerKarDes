from app.domains.consumer_trust.service import ConsumerTrustService


def test_rc226_feedback_capture():
    result = ConsumerTrustService().record_feedback(
        user_id="u1",
        recommendation_id="r1",
        feedback_type="HELPFUL",
    )
    assert result["recorded"] is True
