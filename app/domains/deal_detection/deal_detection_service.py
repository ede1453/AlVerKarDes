from app.domains.cache.cache_key_builder import CacheKeyBuilder
from app.domains.cache.cache_service import CacheService
from app.domains.deal_detection.deal_detection_engine import DealDetectionEngine
from app.domains.deal_detection.deal_detection_models import DealDetectionResult, create_deal_id
from app.domains.deal_detection.deal_detection_serializer import serialize_deal_detection_result
from app.domains.events.event_bus_service import EventBusService


class DealDetectionService:
    def __init__(
        self,
        engine: DealDetectionEngine | None = None,
        cache_service: CacheService | None = None,
        event_bus_service: EventBusService | None = None,
    ):
        self.engine = engine or DealDetectionEngine()
        self.cache_service = cache_service or CacheService()
        self.event_bus_service = event_bus_service or EventBusService()
        self.key_builder = CacheKeyBuilder()

    def detect(self, payload: dict):
        decision = self.engine.detect(
            product_key=payload["product_key"],
            offer=payload["offer"],
            price_history=payload.get("price_history"),
            personalization=payload.get("personalization"),
        )

        result = DealDetectionResult(
            deal_id=create_deal_id(),
            product_key=payload["product_key"],
            offer=payload["offer"],
            deal_level=decision["deal_level"],
            deal_score=decision["deal_score"],
            price_signal=decision["price_signal"],
            personalization_signal=decision["personalization_signal"],
            confidence=decision["confidence"],
            reasons=decision["reasons"],
            next_actions=decision["next_actions"],
            metadata={"deal_detection_version": "deal_detection_v1"},
        )

        serialized = serialize_deal_detection_result(result)

        self.event_bus_service.publish(
            {
                "event_type": "deal_detection.completed",
                "source": "deal_detection",
                "payload": {
                    "deal_id": serialized["deal_id"],
                    "product_key": serialized["product_key"],
                    "deal_level": serialized["deal_level"],
                    "deal_score": serialized["deal_score"],
                },
                "metadata": {"event_version": "event_v1"},
            }
        )

        return serialized

    def detect_cached(self, payload: dict):
        cache_key = self.key_builder.build(
            namespace="deal_detection",
            payload={
                "product_key": payload["product_key"],
                "offer": payload.get("offer"),
                "price_history": payload.get("price_history"),
                "personalization": payload.get("personalization"),
            },
        )

        return self.cache_service.get_or_set(
            key=cache_key,
            value_factory=lambda: self.detect(payload),
            ttl_seconds=payload.get("ttl_seconds", 300),
        )
