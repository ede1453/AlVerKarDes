from app.domains.consumer_trust.service import ConsumerTrustService


def test_rc240_consumer_trust_dashboard():
    result = ConsumerTrustService().build_trust_dashboard(
        recommendation_count=100,
        audited_count=100,
        passed_audit_count=95,
        feedback_count=100,
        helpful_feedback_count=90,
        false_positive_count=2,
        disclosure_compliance_pct=100,
    )
    assert result["trust_score"] >= 90
    assert result["status"] == "EXCELLENT"
