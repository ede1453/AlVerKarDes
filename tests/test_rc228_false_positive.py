from app.domains.consumer_trust.service import ConsumerTrustService


def test_rc228_false_positive():
    result = ConsumerTrustService().report_false_positive(
        user_id="u1",
        deal_id="d1",
        reason="Price unavailable",
        observed_price=999,
    )
    assert result["feedback"]["metadata"]["false_positive"] is True
