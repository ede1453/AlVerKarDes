from app.domains.ai_shopping_assistant.assistant_engine import AIShoppingAssistantEngine
from app.domains.ai_shopping_assistant.assistant_models import ShoppingAssistantInput


def test_ai_shopping_assistant_engine_returns_buy_now():
    result = AIShoppingAssistantEngine().advise(
        ShoppingAssistantInput(
            product_name="MacBook Air",
            final_decision="BUY_NOW",
            confidence=94,
            risk_level="LOW",
            opportunity_level="HIGH",
            reason_codes=["STRONG_BUY_SIGNAL"],
            trust_score=90,
        )
    )

    assert result.assistant_decision == "BUY_NOW"
    assert result.headline == "Buy MacBook Air now"
    assert "ASSISTANT_BUY_SIGNAL" in result.reason_codes
    assert result.next_actions


def test_ai_shopping_assistant_engine_blocks_high_risk_purchase():
    result = AIShoppingAssistantEngine().advise(
        ShoppingAssistantInput(
            product_name="Unknown Laptop",
            final_decision="BUY_NOW",
            confidence=96,
            risk_level="HIGH",
            trust_score=20,
        )
    )

    assert result.assistant_decision == "DO_NOT_BUY"
    assert "ASSISTANT_RISK_BLOCK" in result.reason_codes


def test_ai_shopping_assistant_engine_uses_personalized_decision():
    result = AIShoppingAssistantEngine().advise(
        ShoppingAssistantInput(
            product_name="Headphones",
            final_decision="BUY_NOW",
            confidence=90,
            personalized_decision="WATCH",
            personalized_confidence=75,
            personalization_reasons=["HIGH_PRICE_SENSITIVITY_REQUIRES_STRONG_OPPORTUNITY"],
        )
    )

    assert result.assistant_decision == "WATCH"
    assert result.confidence == 75
    assert "HIGH_PRICE_SENSITIVITY_REQUIRES_STRONG_OPPORTUNITY" in result.reason_codes
