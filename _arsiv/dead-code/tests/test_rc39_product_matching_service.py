from app.domains.events.event_repository_factory import reset_event_repository
from app.domains.product_matching.product_matching_service import ProductMatchingService


def test_product_matching_service_emits_event():
    reset_event_repository()
    service = ProductMatchingService()

    result = service.match(
        {
            "query": "MacBook Air",
            "offers": [
                {"id": "1", "marketplace": "amazon", "product_name": "MacBook Air M3 13", "price": "999.00"},
                {"id": "2", "marketplace": "saturn", "product_name": "MacBook Air M3 13", "price": "949.00"},
            ],
        }
    )

    assert result["group_count"] == 1

    events = service.event_bus_service.list_recent(
        {"event_type": "product_matching.completed", "source": "product_matching"}
    )

    assert events
    assert events[0]["payload"]["group_count"] == 1


def test_product_matching_service_cache_hit_on_second_call():
    service = ProductMatchingService()
    payload = {
        "query": "MacBook Air",
        "offers": [
            {"id": "1", "marketplace": "amazon", "product_name": "MacBook Air M3 13", "price": "999.00"},
        ],
        "ttl_seconds": 300,
    }

    first = service.match_cached(payload)
    second = service.match_cached(payload)

    assert first["cache_hit"] is False
    assert second["cache_hit"] is True
