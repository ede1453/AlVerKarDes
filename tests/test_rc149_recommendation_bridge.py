from app.domains.deal_intelligence.service import RecommendationBridge


def test_rc149_buy_recommendation():
    result = RecommendationBridge().build(
        opportunity={
            "source_id":"amazon",
            "canonical_product_key":"apple::macbook-air::m5",
            "confidence_score":85,
            "truth_status":"GENUINE_STRONG_DISCOUNT",
            "observed_discount_pct":25,
            "source_confidence":90,
            "freshness_status":"FRESH",
            "anomaly_detected":False,
            "effective_price":899,
        }
    )
    assert result["decision"] == "BUY"
    assert result["confidence"] == 85.0

def test_rc149_anomaly_do_not_buy():
    result = RecommendationBridge().build(
        opportunity={
            "confidence_score":90,
            "truth_status":"GENUINE_STRONG_DISCOUNT",
            "anomaly_detected":True,
        }
    )
    assert result["decision"] == "DO_NOT_BUY"
