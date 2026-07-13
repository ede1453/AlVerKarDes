from app.domains.deal_detection.deal_detection_engine import DealDetectionEngine


def test_deal_detection_engine_detects_excellent_deal():
    result = DealDetectionEngine().detect(
        product_key="macbook-air",
        offer={"price": "949.00", "marketplace": "saturn"},
        price_history={"min_price": "949.00", "average_price": "999.00", "latest_price": "949.00", "trend": "DOWN"},
        personalization={"top_offer": {"personalization_score": 95}},
    )

    assert result["deal_level"] == "EXCELLENT_DEAL"
    assert result["deal_score"] >= 85
    assert "PRICE_AT_HISTORY_LOW" in result["reasons"]


def test_deal_detection_engine_detects_weak_deal():
    result = DealDetectionEngine().detect(
        product_key="macbook-air",
        offer={"price": "1099.00", "marketplace": "amazon"},
        price_history={"min_price": "949.00", "average_price": "999.00", "latest_price": "1099.00", "trend": "UP"},
        personalization={"top_offer": {"personalization_score": 30}},
    )

    assert result["deal_level"] == "WEAK_DEAL"
