from app.domains.ai_shopping_assistant.assistant_engine import AIShoppingAssistantEngine
from app.domains.ai_shopping_assistant.assistant_models import ShoppingAssistantInput
from app.domains.ai_shopping_assistant.assistant_serializer import (
    serialize_shopping_assistant_advice,
)


class AIShoppingAssistantService:
    def __init__(self, engine: AIShoppingAssistantEngine | None = None):
        self.engine = engine or AIShoppingAssistantEngine()

    def advise(self, payload: dict):
        advice = self.engine.advise(
            ShoppingAssistantInput(
                user_id=payload.get("user_id"),
                query=payload.get("query"),
                product_name=payload.get("product_name"),
                product_brand=payload.get("product_brand"),
                product_category=payload.get("product_category"),
                current_price=payload.get("current_price"),
                currency=payload.get("currency", "EUR"),
                final_decision=payload.get("final_decision", "WATCH"),
                confidence=payload.get("confidence", 70),
                risk_level=payload.get("risk_level"),
                opportunity_level=payload.get("opportunity_level"),
                reason_codes=payload.get("reason_codes", []),
                explanation=payload.get("explanation", []),
                personalized_decision=payload.get("personalized_decision"),
                personalized_confidence=payload.get("personalized_confidence"),
                personalization_reasons=payload.get("personalization_reasons", []),
                trust_score=payload.get("trust_score"),
                community_score=payload.get("community_score"),
                metadata=payload.get("metadata", {}),
            )
        )

        return serialize_shopping_assistant_advice(advice)
