from app.domains.cache.cache_repository_factory import get_cache_repository
from app.domains.events.event_repository_factory import reset_event_repository
from app.domains.price_history.price_history_service import PriceHistoryService


def test_price_history_service_adds_point_and_emits_event():
    reset_event_repository()
    service = PriceHistoryService()

    point = service.add_point(
        {
            "product_key": "macbook-air",
            "marketplace": "amazon",
            "price": "999.00",
            "currency": "EUR",
        }
    )

    assert point["product_key"] == "macbook-air"

    events = service.event_bus_service.list_recent(
        {"event_type": "price_history.point_added", "source": "price_history"}
    )
    assert events


def test_price_history_service_summary_cached_hits_second_time():
    cache = get_cache_repository()
    cache.clear()

    service = PriceHistoryService()

    service.add_point(
        {
            "product_key": "macbook-air",
            "marketplace": "amazon",
            "price": "999.00"
        }
    )

    payload = {
        "product_key": "macbook-air",
        "ttl_seconds": 300
    }

    first = service.summary_cached(payload)
    second = service.summary_cached(payload)

    assert first["cache_hit"] is False
    assert second["cache_hit"] is True
