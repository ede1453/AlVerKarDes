from app.domains.consumer_trust.service import ConsumerTrustService


def test_rc234_deal_comparison():
    result = ConsumerTrustService().compare_deals(
        deals=[
            {
                "deal_id":"d1",
                "confidence_score":80,
                "observed_discount_pct":20,
                "effective_price":900,
            },
            {
                "deal_id":"d2",
                "confidence_score":90,
                "observed_discount_pct":25,
                "effective_price":950,
            },
        ]
    )
    assert result["best_deal"]["deal_id"] == "d2"
