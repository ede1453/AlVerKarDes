from app.domains.cache.cache_key_builder import CacheKeyBuilder
from app.domains.cache.cache_service import CacheService
from app.domains.events.event_bus_service import EventBusService
from app.domains.product_matching.product_matching_engine import ProductMatchingEngine
from app.domains.product_matching.product_matching_serializer import serialize_matching_result


class ProductMatchingService:
    def __init__(
        self,
        engine: ProductMatchingEngine | None = None,
        cache_service: CacheService | None = None,
        event_bus_service: EventBusService | None = None,
    ):
        self.engine = engine or ProductMatchingEngine()
        self.cache_service = cache_service or CacheService()
        self.event_bus_service = event_bus_service or EventBusService()
        self.key_builder = CacheKeyBuilder()

    def match(self, payload: dict):
        result = self.engine.match(
            query=payload["query"],
            offers=payload.get("offers", []),
        )
        serialized = serialize_matching_result(result)

        self.event_bus_service.publish(
            {
                "event_type": "product_matching.completed",
                "source": "product_matching",
                "payload": {
                    "query": serialized["query"],
                    "group_count": serialized["group_count"],
                    "matched_offer_count": serialized["matched_offer_count"],
                },
                "metadata": {"event_version": "event_v1"},
            }
        )

        return serialized

    def match_cached(self, payload: dict):
        cache_key = self.key_builder.build(
            namespace="product_matching",
            payload={"query": payload["query"], "offers": payload.get("offers", [])},
        )

        return self.cache_service.get_or_set(
            key=cache_key,
            value_factory=lambda: self.match(payload),
            ttl_seconds=payload.get("ttl_seconds", 300),
        )
