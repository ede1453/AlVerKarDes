from app.domains.cache.cache_key_builder import CacheKeyBuilder
from app.domains.cache.cache_service import CacheService
from app.domains.events.event_bus_service import EventBusService
from app.domains.marketplace_aggregation.marketplace_service import MarketplaceAggregationService
from app.domains.unified_search.unified_search_models import (
    UnifiedSearchResult,
    create_search_id,
    now_utc,
)
from app.domains.unified_search.unified_search_serializer import (
    serialize_unified_search_result,
)


class UnifiedSearchService:
    def __init__(
        self,
        marketplace_service: MarketplaceAggregationService | None = None,
        cache_service: CacheService | None = None,
        event_bus_service: EventBusService | None = None,
    ):
        self.marketplace_service = marketplace_service or MarketplaceAggregationService()
        self.cache_service = cache_service or CacheService()
        self.event_bus_service = event_bus_service or EventBusService()
        self.key_builder = CacheKeyBuilder()

    def search(self, payload: dict):
        aggregation = self.marketplace_service.aggregate(
            {
                "query": payload["query"],
                "offers": payload.get("offers", []),
            }
        )

        top_offer = aggregation["offers"][0] if aggregation["offers"] else None
        status = "FOUND" if top_offer else "NO_RESULTS"

        result = UnifiedSearchResult(
            search_id=create_search_id(),
            query=payload["query"],
            user_id=payload.get("user_id"),
            status=status,
            aggregation=aggregation,
            top_offer=top_offer,
            candidate_count=aggregation["offer_count"],
            metadata={
                "marketplaces": aggregation["marketplaces"],
                "requested_marketplaces": payload.get("marketplaces", []),
                "search_version": "unified_search_v1",
                **payload.get("metadata", {}),
            },
            created_at=now_utc(),
        )

        serialized = serialize_unified_search_result(result)

        self.event_bus_service.publish(
            {
                "event_type": "unified_search.completed",
                "source": "unified_search",
                "payload": {
                    "search_id": serialized["search_id"],
                    "query": serialized["query"],
                    "status": serialized["status"],
                    "candidate_count": serialized["candidate_count"],
                },
                "metadata": {"event_version": "event_v1"},
            }
        )

        return serialized

    def search_cached(self, payload: dict):
        cache_key = self.key_builder.build(
            namespace="unified_search",
            payload={
                "query": payload["query"],
                "user_id": payload.get("user_id"),
                "marketplaces": payload.get("marketplaces", []),
                "offers": payload.get("offers", []),
            },
        )

        return self.cache_service.get_or_set(
            key=cache_key,
            value_factory=lambda: self.search(payload),
            ttl_seconds=payload.get("ttl_seconds", 300),
        )
