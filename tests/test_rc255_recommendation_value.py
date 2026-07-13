from app.domains.user_value.service import UserValueIntelligenceService


def test_rc255_value():
    result = UserValueIntelligenceService().calculate_recommendation_value(
        savings_amount=200,
        confidence=90,
        user_relevance_score=80,
        false_positive_risk=10,
    )

    assert result["value_score"] >= 70
