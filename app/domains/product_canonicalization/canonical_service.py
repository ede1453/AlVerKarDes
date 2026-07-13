from app.domains.cache.cache_key_builder import CacheKeyBuilder
from app.domains.cache.cache_service import CacheService
from app.domains.events.event_bus_service import EventBusService
from app.domains.product_canonicalization.canonical_engine import ProductCanonicalizationEngine
from app.domains.product_canonicalization.canonical_serializer import (
    serialize_canonicalization_result,
)


class ProductCanonicalizationService:
    def __init__(
        self,
        engine: ProductCanonicalizationEngine | None = None,
        cache_service: CacheService | None = None,
        event_bus_service: EventBusService | None = None,
    ):
        self.engine = engine or ProductCanonicalizationEngine()
        self.cache_service = cache_service or CacheService()
        self.event_bus_service = event_bus_service or EventBusService()
        self.key_builder = CacheKeyBuilder()

    def canonicalize(self, payload: dict):
        result = self.engine.canonicalize(
            query=payload["query"],
            offers=payload.get("offers", []),
        )
        serialized = serialize_canonicalization_result(result)

        self.event_bus_service.publish(
            {
                "event_type": "product_canonicalization.completed",
                "source": "product_canonicalization",
                "payload": {
                    "query": serialized["query"],
                    "canonical_count": serialized["canonical_count"],
                },
                "metadata": {"event_version": "event_v1"},
            }
        )

        return serialized

    def canonicalize_cached(self, payload: dict):
        cache_key = self.key_builder.build(
            namespace="product_canonicalization",
            payload={"query": payload["query"], "offers": payload.get("offers", [])},
        )
        return self.cache_service.get_or_set(
            key=cache_key,
            value_factory=lambda: self.canonicalize(payload),
            ttl_seconds=payload.get("ttl_seconds", 300),
        )
