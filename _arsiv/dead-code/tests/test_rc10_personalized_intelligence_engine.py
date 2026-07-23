from app.domains.personalized_intelligence.personalization_models import (
    PersonalizedDecisionInput,
    UserPreferenceProfile,
)
from app.domains.personalized_intelligence.personalized_intelligence_engine import (
    PersonalizedIntelligenceEngine,
)


def test_personalized_engine_avoids_user_avoided_brand():
    result = PersonalizedIntelligenceEngine().personalize(
        profile=UserPreferenceProfile(
            user_id="user-1",
            avoided_brands=["brand-x"],
        ),
        decision=PersonalizedDecisionInput(
            user_id="user-1",
            final_decision="BUY_NOW",
            confidence=94,
            product_brand="brand-x",
        ),
    )

    assert result.personalized_decision == "AVOID"
    assert "USER_AVOIDS_BRAND" in result.personalization_reasons


def test_personalized_engine_boosts_preferred_brand():
    result = PersonalizedIntelligenceEngine().personalize(
        profile=UserPreferenceProfile(
            user_id="user-1",
            preferred_brands=["apple"],
        ),
        decision=PersonalizedDecisionInput(
            user_id="user-1",
            final_decision="BUY_NOW",
            confidence=90,
            product_brand="apple",
        ),
    )

    assert result.personalized_decision == "BUY_NOW"
    assert result.personalized_confidence == 95
    assert "USER_PREFERS_BRAND" in result.personalization_reasons


def test_personalized_engine_converts_buy_to_watch_for_high_price_sensitivity():
    result = PersonalizedIntelligenceEngine().personalize(
        profile=UserPreferenceProfile(
            user_id="user-1",
            price_sensitivity="HIGH",
        ),
        decision=PersonalizedDecisionInput(
            user_id="user-1",
            final_decision="BUY_NOW",
            confidence=88,
            opportunity_level="MEDIUM",
        ),
    )

    assert result.personalized_decision == "WATCH"
    assert "HIGH_PRICE_SENSITIVITY_REQUIRES_STRONG_OPPORTUNITY" in result.personalization_reasons
