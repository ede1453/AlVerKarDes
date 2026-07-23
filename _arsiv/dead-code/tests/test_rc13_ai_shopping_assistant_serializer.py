from app.domains.ai_shopping_assistant.assistant_models import ShoppingAssistantAdvice
from app.domains.ai_shopping_assistant.assistant_serializer import (
    serialize_shopping_assistant_advice,
)


def test_ai_shopping_assistant_serializer():
    data = serialize_shopping_assistant_advice(
        ShoppingAssistantAdvice(
            assistant_decision="WATCH",
            headline="Watch this product",
            summary="Signals are mixed.",
            confidence=72,
            risk_level="MEDIUM",
            opportunity_level="MEDIUM",
            next_actions=["Set a price alert."],
            reason_codes=["ASSISTANT_WATCH_SIGNAL"],
            explanation=["Signals are mixed."],
            assistant_context={"product_name": "Phone"},
        )
    )

    assert data["assistant_decision"] == "WATCH"
    assert data["next_actions"] == ["Set a price alert."]
