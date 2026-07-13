from app.domains.decision_context.decision_context_builder import (
    DecisionContextBuilder,
    DecisionContextInput,
)
from app.domains.decision_context.decision_context_serializer import (
    serialize_decision_context,
)


class DecisionContextService:
    def __init__(self, builder: DecisionContextBuilder | None = None):
        self.builder = builder or DecisionContextBuilder()

    def build(self, payload: dict):
        context = self.builder.build(
            DecisionContextInput(
                product_id=payload.get("product_id"),
                offer_id=payload.get("offer_id"),
                country=payload.get("country", "DE"),
                currency=payload.get("currency", "EUR"),
                deal_score=payload.get("deal_score"),
                authenticity_score=payload.get("authenticity_score"),
                recommendation=payload.get("recommendation"),
                recommendation_confidence=payload.get("recommendation_confidence"),
                final_decision=payload.get("final_decision"),
                risk_level=payload.get("risk_level"),
                opportunity_level=payload.get("opportunity_level"),
                reason_codes=payload.get("reason_codes", []),
                explanation=payload.get("explanation", []),
                metadata=payload.get("metadata", {}),
            )
        )

        return serialize_decision_context(context)
