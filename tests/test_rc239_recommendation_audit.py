from app.domains.consumer_trust.service import ConsumerTrustService


def test_rc239_recommendation_audit():
    result = ConsumerTrustService().audit_recommendation(
        recommendation_id="r1",
        decision="BUY",
        evidence={
            "source_confidence":90,
            "affiliate_enabled":True,
        },
        affiliate_disclosure_present=True,
        sponsored=False,
        ranking_influenced=False,
    )
    assert result["passed"] is True
