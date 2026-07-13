from app.domains.ai_shopping_assistant.assistant_service import AIShoppingAssistantService


def test_ai_shopping_assistant_service_serializes_advice():
    data = AIShoppingAssistantService().advise(
        {
            "product_name": "MacBook Air",
            "final_decision": "BUY_NOW",
            "confidence": 94,
            "risk_level": "LOW",
            "opportunity_level": "HIGH",
            "reason_codes": ["STRONG_BUY_SIGNAL"],
            "trust_score": 90,
        }
    )

    assert data["assistant_decision"] == "BUY_NOW"
    assert data["assistant_context"]["product_name"] == "MacBook Air"
    assert data["next_actions"]
