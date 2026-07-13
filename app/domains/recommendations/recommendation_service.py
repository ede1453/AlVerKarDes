from app.domains.cache.cache_key_builder import CacheKeyBuilder
from app.domains.cache.cache_service import CacheService
from app.domains.events.event_bus_service import EventBusService
from app.domains.recommendations.recommendation_engine import RecommendationEngine
from app.domains.recommendations.recommendation_models import (
    RecommendationItem,
    RecommendationResult,
    create_recommendation_id,
    create_recommendation_run_id,
)
from app.domains.recommendations.recommendation_serializer import serialize_recommendation_result


class RecommendationService:
    def __init__(
        self,
        engine: RecommendationEngine | None = None,
        cache_service: CacheService | None = None,
        event_bus_service: EventBusService | None = None,
    ):
        self.engine = engine or RecommendationEngine()
        self.cache_service = cache_service or CacheService()
        self.event_bus_service = event_bus_service or EventBusService()
        self.key_builder = CacheKeyBuilder()

    def recommend(self, payload: dict):
        data = self.engine.recommend(
            query=payload["query"],
            user_id=payload.get("user_id"),
            candidates=payload.get("candidates", []),
            personalization=payload.get("personalization"),
            discount_intelligence=payload.get("discount_intelligence"),
            deal_detection=payload.get("deal_detection"),
            price_prediction=payload.get("price_prediction"),
        )

        items = []
        for index, scored in enumerate(data["items"], start=1):
            candidate = scored["candidate"]
            items.append(
                RecommendationItem(
                    recommendation_id=create_recommendation_id(),
                    product_key=candidate.get("product_key") or candidate.get("canonical_key") or "",
                    product_name=candidate.get("product_name") or "",
                    recommendation_type=scored["recommendation_type"],
                    score=scored["score"],
                    rank=index,
                    rationale=scored["rationale"],
                    source=candidate,
                    metadata={"recommendation_version": "recommendation_v1"},
                )
            )

        result = RecommendationResult(
            run_id=create_recommendation_run_id(),
            user_id=payload.get("user_id"),
            query=payload["query"],
            status=data["status"],
            items=items,
            next_actions=data["next_actions"],
            metadata={"recommendation_version": "recommendation_v1"},
        )

        serialized = serialize_recommendation_result(result)

        self.event_bus_service.publish(
            {
                "event_type": "recommendation.generated",
                "source": "recommendations",
                "payload": {
                    "run_id": serialized["run_id"],
                    "query": serialized["query"],
                    "status": serialized["status"],
                    "item_count": len(serialized["items"]),
                },
                "metadata": {"event_version": "event_v1"},
            }
        )

        return serialized

    def recommend_cached(self, payload: dict):
        cache_key = self.key_builder.build(
            namespace="recommendations",
            payload={
                "query": payload["query"],
                "user_id": payload.get("user_id"),
                "candidates": payload.get("candidates", []),
                "personalization": payload.get("personalization"),
                "discount_intelligence": payload.get("discount_intelligence"),
                "deal_detection": payload.get("deal_detection"),
                "price_prediction": payload.get("price_prediction"),
            },
        )
        return self.cache_service.get_or_set(
            key=cache_key,
            value_factory=lambda: self.recommend(payload),
            ttl_seconds=payload.get("ttl_seconds", 300),
        )
