from app.domains.decision_memory.decision_memory_models import (
    DecisionMemoryCreate,
    create_decision_memory_record,
)


class DecisionMemoryEngine:
    def create_record(self, payload: dict):
        return create_decision_memory_record(
            DecisionMemoryCreate(
                user_id=payload.get("user_id"),
                product_id=payload.get("product_id"),
                offer_id=payload.get("offer_id"),
                country=payload.get("country", "DE"),
                final_decision=payload.get("final_decision", "WATCH"),
                confidence=payload.get("confidence", 0),
                risk_level=payload.get("risk_level"),
                opportunity_level=payload.get("opportunity_level"),
                deal_score=payload.get("deal_score"),
                authenticity_score=payload.get("authenticity_score"),
                recommendation=payload.get("recommendation"),
                reason_codes=payload.get("reason_codes", []),
                decision_context=payload.get("decision_context", {}),
            )
        )
