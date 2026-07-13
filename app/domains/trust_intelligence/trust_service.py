from app.domains.trust_intelligence.trust_engine import TrustIntelligenceEngine
from app.domains.trust_intelligence.trust_models import TrustEvaluationInput, TrustSignal
from app.domains.trust_intelligence.trust_repository import TrustRepository
from app.domains.trust_intelligence.trust_serializer import (
    serialize_trust_evaluation,
    serialize_trust_profile,
    serialize_trust_signal,
)


class TrustIntelligenceService:
    def __init__(
        self,
        repository: TrustRepository | None = None,
        engine: TrustIntelligenceEngine | None = None,
    ):
        self.repository = repository or TrustRepository()
        self.engine = engine or TrustIntelligenceEngine()

    async def upsert_signal(self, payload: dict):
        signal = TrustSignal(
            source_type=payload["source_type"],
            source_id=payload["source_id"],
            positive_count=payload.get("positive_count", 0),
            negative_count=payload.get("negative_count", 0),
            neutral_count=payload.get("neutral_count", 0),
            fraud_count=payload.get("fraud_count", 0),
            return_count=payload.get("return_count", 0),
            total_count=payload.get("total_count", 0),
        )
        saved = await self.repository.save_signal(signal)
        profile = self.engine.build_profile(
            entity_type=saved.source_type,
            entity_id=saved.source_id,
            signal=saved,
        )
        await self.repository.save_profile(profile)
        return {
            "signal": serialize_trust_signal(saved),
            "profile": serialize_trust_profile(profile),
        }

    async def get_profile(self, entity_type: str, entity_id: str):
        profile = await self.repository.get_profile(entity_type, entity_id)
        if profile is None:
            return None
        return serialize_trust_profile(profile)

    async def evaluate(self, payload: dict):
        user_profile = await self._get_optional_profile("user", payload.get("user_id"))
        store_profile = await self._get_optional_profile("store", payload.get("store_id"))
        product_profile = await self._get_optional_profile("product", payload.get("product_id"))
        community_profile = await self._get_optional_profile("community", payload.get("community_id", "global"))

        result = self.engine.evaluate(
            data=TrustEvaluationInput(
                decision_id=payload.get("decision_id"),
                user_id=payload.get("user_id"),
                store_id=payload.get("store_id"),
                product_id=payload.get("product_id"),
                base_confidence=payload.get("base_confidence", 70),
                final_decision=payload.get("final_decision", "WATCH"),
                feedback_summary=payload.get("feedback_summary", {}),
            ),
            user_profile=user_profile,
            store_profile=store_profile,
            product_profile=product_profile,
            community_profile=community_profile,
        )
        return serialize_trust_evaluation(result)

    async def _get_optional_profile(self, entity_type: str, entity_id: str | None):
        if not entity_id:
            return None
        return await self.repository.get_profile(entity_type, entity_id)
