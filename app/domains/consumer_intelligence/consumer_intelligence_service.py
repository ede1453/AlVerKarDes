from app.domains.consumer_intelligence.consumer_intelligence_engine import (
    ConsumerIntelligenceEngine,
    ConsumerIntelligenceInput,
)
from app.domains.consumer_intelligence.consumer_intelligence_serializer import (
    serialize_consumer_intelligence,
)


class ConsumerIntelligenceService:
    def __init__(self, engine: ConsumerIntelligenceEngine | None = None):
        self.engine = engine or ConsumerIntelligenceEngine()

    def evaluate(self, payload: dict):
        result = self.engine.evaluate(
            ConsumerIntelligenceInput(
                deal_score=payload["deal_score"],
                authenticity_score=payload["authenticity_score"],
                recommendation=payload["recommendation"],
                recommendation_confidence=payload["recommendation_confidence"],
                trend_direction=payload.get("trend_direction"),
                store_trust_score=payload.get("store_trust_score"),
                stock_status=payload.get("stock_status"),
                reason_codes=payload.get("reason_codes", []),
            )
        )

        return serialize_consumer_intelligence(result)
