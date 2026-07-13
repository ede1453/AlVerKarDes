from app.domains.deal_intelligence.service import DealConfidenceEngine


def test_rc147_high_deal_confidence():
    result = DealConfidenceEngine().calculate(
        discount_truth={
            "truth_status":"GENUINE_STRONG_DISCOUNT"
        },
        source_confidence=90,
        freshness_status="FRESH",
        anomaly_detected=False,
        review_reliability=80,
    )
    assert result["confidence_score"] >= 80
    assert result["confidence_level"] == "VERY_HIGH"

def test_rc147_anomaly_penalty():
    result = DealConfidenceEngine().calculate(
        discount_truth={
            "truth_status":"GENUINE_STRONG_DISCOUNT"
        },
        source_confidence=90,
        freshness_status="FRESH",
        anomaly_detected=True,
        review_reliability=80,
    )
    assert result["confidence_score"] < 80
