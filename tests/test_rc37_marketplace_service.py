from app.domains.events.event_repository_factory import reset_event_repository
from app.domains.marketplace_aggregation.marketplace_service import MarketplaceAggregationService


def test_marketplace_service_aggregate_emits_event():
    reset_event_repository()
    service = MarketplaceAggregationService()

    result = service.aggregate({
        "query": "MacBook Air",
        "offers": [{"marketplace": "amazon", "seller": "Amazon", "product_name": "MacBook Air M3", "price": "999.00"}],
    })

    assert result["offer_count"] == 1
    events = service.event_bus_service.list_recent({"event_type": "marketplace.aggregation.completed", "source": "marketplace_aggregation"})
    assert events


def test_marketplace_service_cached_returns_hit_on_second_call():
    service = MarketplaceAggregationService()
    payload = {
        "query": "MacBook Air",
        "offers": [{"marketplace": "amazon", "seller": "Amazon", "product_name": "MacBook Air M3", "price": "999.00"}],
        "ttl_seconds": 300,
    }

    first = service.aggregate_cached(payload)
    second = service.aggregate_cached(payload)

    assert first["cache_hit"] is False
    assert second["cache_hit"] is True
