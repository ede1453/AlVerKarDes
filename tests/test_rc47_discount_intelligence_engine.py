from app.domains.discount_intelligence.discount_engine import DiscountIntelligenceEngine


def test_discount_engine_detects_real_discount_low_fake_risk():
    result = DiscountIntelligenceEngine().analyze(
        product_key="macbook-air",
        current_price="949.00",
        claimed_original_price="1099.00",
        price_history={"min_price": "949.00", "average_price": "999.00", "max_price": "1099.00", "trend": "DOWN"},
        deal_detection={"deal_score": 95},
        price_prediction={"recommendation_hint": "BUY_SOON"},
    )

    assert result["discount_quality"] == "EXCELLENT_REAL_DISCOUNT"
    assert result["fake_discount_risk"] == "LOW"
    assert result["effective_discount_percent"] == 14


def test_discount_engine_flags_high_fake_risk_when_claimed_price_above_history():
    result = DiscountIntelligenceEngine().analyze(
        product_key="macbook-air",
        current_price="999.00",
        claimed_original_price="1499.00",
        price_history={"min_price": "949.00", "average_price": "999.00", "max_price": "1099.00", "trend": "UP"},
        deal_detection={"deal_score": 40},
        price_prediction={"recommendation_hint": "WAIT_OR_WATCH"},
    )

    assert result["fake_discount_risk"] in ["MEDIUM", "HIGH"]
    assert "CLAIMED_ORIGINAL_ABOVE_HISTORY_MAX" in result["reasons"]
