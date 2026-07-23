from app.domains.cache.cache_key_builder import CacheKeyBuilder
from app.domains.cache.cache_service import CacheService
from app.domains.events.event_bus_service import EventBusService
from app.domains.price_history.price_history_engine import PriceHistoryEngine
from app.domains.price_history.price_history_models import create_price_point
from app.domains.price_history.price_history_repository import InMemoryPriceHistoryRepository
from app.domains.price_history.price_history_serializer import (
    serialize_price_history_summary,
    serialize_price_point,
)


class PriceHistoryService:
    def __init__(
        self,
        repository: InMemoryPriceHistoryRepository | None = None,
        engine: PriceHistoryEngine | None = None,
        event_bus_service: EventBusService | None = None,
        cache_service: CacheService | None = None,
    ):
        self.repository = repository or InMemoryPriceHistoryRepository()
        self.engine = engine or PriceHistoryEngine()
        self.event_bus_service = event_bus_service or EventBusService()
        self.cache_service = cache_service or CacheService()
        self.key_builder = CacheKeyBuilder()

    def add_point(self, payload: dict):
        point = self.repository.add(create_price_point(payload))

        self.event_bus_service.publish(
            {
                "event_type": "price_history.point_added",
                "source": "price_history",
                "payload": {
                    "product_key": point.product_key,
                    "marketplace": point.marketplace,
                    "price": str(point.price),
                    "currency": point.currency,
                },
                "metadata": {"event_version": "event_v1"},
            }
        )

        return serialize_price_point(point)

    def bulk_add(self, payload: dict):
        points = [self.add_point(item) for item in payload.get("points", [])]
        return {"added_count": len(points), "points": points}

    def summary(self, product_key: str):
        points = self.repository.list_for_product(product_key)
        summary = self.engine.summarize(product_key=product_key, points=points)
        return serialize_price_history_summary(summary)

    def summary_cached(self, payload: dict):
        product_key = payload["product_key"]
        cache_key = self.key_builder.build(
            namespace="price_history_summary",
            payload={"product_key": product_key},
        )
        return self.cache_service.get_or_set(
            key=cache_key,
            value_factory=lambda: self.summary(product_key),
            ttl_seconds=payload.get("ttl_seconds", 300),
        )

    def clear(self):
        self.repository.clear()
        return {"cleared": True}
