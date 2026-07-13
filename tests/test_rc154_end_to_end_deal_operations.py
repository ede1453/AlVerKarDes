from app.domains.deal_operations.service import DealDecisionOperationsService


def test_rc154_end_to_end_deal_operations():
    service = DealDecisionOperationsService()
    service.repository.add_watchlist_item(
        user_id="user-1",
        product_key="apple::macbook-air::m5",
        target_price=750,
        minimum_confidence=70,
    )
    result = service.evaluate_and_store(
        user_id="user-1",
        opportunities=[{
            "source_id":"amazon",
            "canonical_product_key":"apple::macbook-air::m5",
            "price":700,
            "claimed_original_price":1000,
            "historical_prices":[950,1000,1050,980],
            "source_confidence":90,
            "freshness_status":"FRESH",
            "anomaly_detected":False,
            "review_reliability":80,
            "effective_price":700,
        }],
    )
    assert result["stored_count"] == 1
    assert result["recommendation"]["decision"] == "BUY"
    assert result["alert"]["should_alert"] is True
    assert result["watchlist_matches"]["match_count"] == 1
