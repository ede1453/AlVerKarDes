from app.domains.deal_lifecycle.service import DealLifecycleService


def test_rc157_watch_policy_match():
    service = DealLifecycleService()
    service.create_watch_policy(
        user_id="user-1",
        product_key="product-1",
        target_price=900,
        minimum_discount_pct=20,
        minimum_confidence=70,
        allowed_sources=["amazon"],
    )
    result = service.evaluate_watch_policies(
        user_id="user-1",
        opportunity={
            "deal_id":"deal-1",
            "canonical_product_key":"product-1",
            "source_id":"amazon",
            "effective_price":850,
            "observed_discount_pct":25,
            "confidence_score":85,
        },
    )
    assert result["match_count"] == 1
