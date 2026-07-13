from app.domains.consumer_intelligence.consumer_intelligence_service import (
    ConsumerIntelligenceService,
)


def test_consumer_intelligence_service_returns_serialized_result():
    data = ConsumerIntelligenceService().evaluate(
        {
            "deal_score": 95,
            "authenticity_score": 96,
            "recommendation": "BUY_NOW",
            "recommendation_confidence": 94,
            "trend_direction": "DOWN",
            "store_trust_score": 90,
            "stock_status": "in_stock",
            "reason_codes": ["HIGH_DEAL_SCORE"],
        }
    )

    assert data["final_decision"] == "BUY_NOW"
    assert data["confidence"] >= 94
    assert data["risk_level"] == "LOW"
    assert data["opportunity_level"] == "HIGH"
