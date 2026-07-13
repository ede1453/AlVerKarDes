from app.domains.analytics.recommendation_intelligence_engine import RecommendationIntelligenceResult
from app.domains.analytics.recommendation_intelligence_serializer import serialize_recommendation_intelligence


def test_recommendation_intelligence_serializer():
    result = RecommendationIntelligenceResult(
        recommendation="BUY_NOW",
        confidence=95,
        reason_codes=["HIGH_DEAL_SCORE"],
        explanation=["Deal score is high."],
    )

    data = serialize_recommendation_intelligence(result)

    assert data["recommendation"] == "BUY_NOW"
    assert data["reason_codes"] == ["HIGH_DEAL_SCORE"]
    assert data["explanation"] == ["Deal score is high."]
