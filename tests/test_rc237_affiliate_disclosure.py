from app.domains.consumer_trust.service import ConsumerTrustService


def test_rc237_affiliate_disclosure():
    result = ConsumerTrustService().build_affiliate_disclosure(
        affiliate_enabled=True,
        commission_possible=True,
    )
    assert result["required"] is True
    assert result["ranking_independent"] is True
