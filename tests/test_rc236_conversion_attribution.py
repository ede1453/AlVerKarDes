from app.domains.consumer_trust.service import ConsumerTrustService


def test_rc236_conversion_attribution():
    result = ConsumerTrustService().attribute_conversion(
        user_id="u1",
        deal_id="d1",
        notification_id="n1",
        order_value=1000,
        affiliate_revenue=20,
    )
    assert result["attributed"] is True
    assert result["conversion"]["affiliate_revenue"] == 20
