from app.domains.cache.cache_key_builder import CacheKeyBuilder
from app.domains.cache.cache_service import CacheService
from app.domains.discount_intelligence.discount_engine import DiscountIntelligenceEngine
from app.domains.discount_intelligence.discount_models import DiscountIntelligenceResult, create_discount_id
from app.domains.discount_intelligence.discount_serializer import serialize_discount_result
from app.domains.events.event_bus_service import EventBusService


class DiscountIntelligenceService:
    def __init__(
        self,
        engine: DiscountIntelligenceEngine | None = None,
        cache_service: CacheService | None = None,
        event_bus_service: EventBusService | None = None,
    ):
        self.engine = engine or DiscountIntelligenceEngine()
        self.cache_service = cache_service or CacheService()
        self.event_bus_service = event_bus_service or EventBusService()
        self.key_builder = CacheKeyBuilder()

    def analyze(self, payload: dict):
        data = self.engine.analyze(
            product_key=payload["product_key"],
            current_price=payload.get("current_price"),
            claimed_original_price=payload.get("claimed_original_price"),
            price_history=payload.get("price_history"),
            deal_detection=payload.get("deal_detection"),
            price_prediction=payload.get("price_prediction"),
        )

        result = DiscountIntelligenceResult(
            discount_id=create_discount_id(),
            product_key=payload["product_key"],
            current_price=data["current_price"],
            claimed_original_price=data["claimed_original_price"],
            effective_discount_percent=data["effective_discount_percent"],
            discount_quality=data["discount_quality"],
            fake_discount_risk=data["fake_discount_risk"],
            confidence=data["confidence"],
            reasons=data["reasons"],
            metadata={"discount_intelligence_version": "discount_intelligence_v1"},
        )

        serialized = serialize_discount_result(result)

        self.event_bus_service.publish(
            {
                "event_type": "discount_intelligence.analyzed",
                "source": "discount_intelligence",
                "payload": {
                    "discount_id": serialized["discount_id"],
                    "product_key": serialized["product_key"],
                    "discount_quality": serialized["discount_quality"],
                    "fake_discount_risk": serialized["fake_discount_risk"],
                    "confidence": serialized["confidence"],
                },
                "metadata": {"event_version": "event_v1"},
            }
        )

        return serialized

    def analyze_cached(self, payload: dict):
        cache_key = self.key_builder.build(
            namespace="discount_intelligence",
            payload={
                "product_key": payload["product_key"],
                "current_price": payload.get("current_price"),
                "claimed_original_price": payload.get("claimed_original_price"),
                "price_history": payload.get("price_history"),
                "deal_detection": payload.get("deal_detection"),
                "price_prediction": payload.get("price_prediction"),
            },
        )

        return self.cache_service.get_or_set(
            key=cache_key,
            value_factory=lambda: self.analyze(payload),
            ttl_seconds=payload.get("ttl_seconds", 300),
        )
