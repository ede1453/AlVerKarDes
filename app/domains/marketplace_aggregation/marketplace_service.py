from app.domains.cache.cache_key_builder import CacheKeyBuilder
from app.domains.cache.cache_service import CacheService
from app.domains.events.event_bus_service import EventBusService
from app.domains.marketplace_aggregation.marketplace_aggregator import MarketplaceAggregator
from app.domains.marketplace_aggregation.marketplace_serializer import (
    serialize_marketplace_aggregation,
)


class MarketplaceAggregationService:
    def __init__(
        self,
        aggregator: MarketplaceAggregator | None = None,
        cache_service: CacheService | None = None,
        event_bus_service: EventBusService | None = None,
    ):
        self.aggregator = aggregator or MarketplaceAggregator()
        self.cache_service = cache_service or CacheService()
        self.event_bus_service = event_bus_service or EventBusService()
        self.key_builder = CacheKeyBuilder()

    def aggregate(self, payload: dict):
        result = self.aggregator.aggregate(
            query=payload["query"],
            offers=payload.get("offers", []),
        )
        serialized = serialize_marketplace_aggregation(result)

        self.event_bus_service.publish(
            {
                "event_type": "marketplace.aggregation.completed",
                "source": "marketplace_aggregation",
                "payload": {
                    "query": serialized["query"],
                    "offer_count": serialized["offer_count"],
                    "marketplaces": serialized["marketplaces"],
                    "min_price": serialized["min_price"],
                    "currency": serialized["currency"],
                },
                "metadata": {"event_version": "event_v1"},
            }
        )

        return serialized

    def aggregate_cached(self, payload: dict):
        cache_key = self.key_builder.build(
            namespace="marketplace_aggregation",
            payload={"query": payload["query"], "offers": payload.get("offers", [])},
        )
        return self.cache_service.get_or_set(
            key=cache_key,
            value_factory=lambda: self.aggregate(payload),
            ttl_seconds=payload.get("ttl_seconds", 300),
        )
