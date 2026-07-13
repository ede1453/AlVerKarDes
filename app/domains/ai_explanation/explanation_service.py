from app.domains.ai_explanation.explanation_engine import AIExplanationEngine
from app.domains.ai_explanation.explanation_models import AIExplanationResult, create_explanation_id
from app.domains.ai_explanation.explanation_prompt_builder import ExplanationPromptBuilder
from app.domains.ai_explanation.explanation_serializer import serialize_explanation
from app.domains.cache.cache_key_builder import CacheKeyBuilder
from app.domains.cache.cache_service import CacheService
from app.domains.events.event_bus_service import EventBusService


class AIExplanationService:
    def __init__(
        self,
        engine: AIExplanationEngine | None = None,
        prompt_builder: ExplanationPromptBuilder | None = None,
        cache_service: CacheService | None = None,
        event_bus_service: EventBusService | None = None,
    ):
        self.engine = engine or AIExplanationEngine()
        self.prompt_builder = prompt_builder or ExplanationPromptBuilder()
        self.cache_service = cache_service or CacheService()
        self.event_bus_service = event_bus_service or EventBusService()
        self.key_builder = CacheKeyBuilder()

    def explain(self, payload: dict):
        data = self.engine.explain(
            language=payload.get("language", "en"),
            tone=payload.get("tone", "clear"),
            agent_decision=payload.get("agent_decision"),
            deal_detection=payload.get("deal_detection"),
            discount_intelligence=payload.get("discount_intelligence"),
            smart_alert=payload.get("smart_alert"),
            price_prediction=payload.get("price_prediction"),
        )

        prompt = self.prompt_builder.build(payload)

        result = AIExplanationResult(
            explanation_id=create_explanation_id(),
            mode=data["mode"],
            language=data["language"],
            tone=data["tone"],
            headline=data["headline"],
            explanation_text=data["explanation_text"],
            bullet_points=data["bullet_points"],
            risk_notes=data["risk_notes"],
            next_actions=data["next_actions"],
            source_signals={
                "agent_decision": payload.get("agent_decision"),
                "deal_detection": payload.get("deal_detection"),
                "discount_intelligence": payload.get("discount_intelligence"),
                "smart_alert": payload.get("smart_alert"),
                "price_prediction": payload.get("price_prediction"),
            },
            metadata={
                "explanation_version": "ai_explanation_v1",
                "prompt": prompt,
            },
        )

        serialized = serialize_explanation(result)

        self.event_bus_service.publish(
            {
                "event_type": "ai_explanation.generated",
                "source": "ai_explanation",
                "payload": {
                    "explanation_id": serialized["explanation_id"],
                    "headline": serialized["headline"],
                    "mode": serialized["mode"],
                    "language": serialized["language"],
                },
                "metadata": {"event_version": "event_v1"},
            }
        )

        return serialized

    def explain_cached(self, payload: dict):
        cache_key = self.key_builder.build(
            namespace="ai_explanation",
            payload={
                "language": payload.get("language", "en"),
                "tone": payload.get("tone", "clear"),
                "agent_decision": payload.get("agent_decision"),
                "deal_detection": payload.get("deal_detection"),
                "discount_intelligence": payload.get("discount_intelligence"),
                "smart_alert": payload.get("smart_alert"),
                "price_prediction": payload.get("price_prediction"),
            },
        )

        return self.cache_service.get_or_set(
            key=cache_key,
            value_factory=lambda: self.explain(payload),
            ttl_seconds=payload.get("ttl_seconds", 300),
        )
