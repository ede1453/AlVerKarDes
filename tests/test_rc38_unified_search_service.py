from app.domains.events.event_repository_factory import reset_event_repository
from app.domains.unified_search.unified_search_service import UnifiedSearchService


def test_unified_search_service_returns_top_offer_and_emits_event():
    reset_event_repository()
    service = UnifiedSearchService()

    result = service.search(
        {
            "query": "MacBook Air",
            "user_id": "user-1",
            "offers": [
                {
                    "marketplace": "amazon",
                    "seller": "Amazon",
                    "product_name": "MacBook Air M3",
                    "price": "999.00",
                    "currency": "EUR",
                },
                {
                    "marketplace": "saturn",
                    "seller": "Saturn",
                    "product_name": "MacBook Air M3",
                    "price": "949.00",
                    "currency": "EUR",
                },
            ],
        }
    )

    assert result["status"] == "FOUND"
    assert result["top_offer"]["marketplace"] == "saturn"
    assert result["candidate_count"] == 2

    events = service.event_bus_service.list_recent(
        {"event_type": "unified_search.completed", "source": "unified_search"}
    )
    assert events
    assert events[0]["payload"]["search_id"] == result["search_id"]


def test_unified_search_service_cached_returns_hit_on_second_call():
    service = UnifiedSearchService()
    payload = {
        "query": "MacBook Air",
        "offers": [
            {
                "marketplace": "amazon",
                "seller": "Amazon",
                "product_name": "MacBook Air M3",
                "price": "999.00",
            }
        ],
        "ttl_seconds": 300,
    }

    first = service.search_cached(payload)
    second = service.search_cached(payload)

    assert first["cache_hit"] is False
    assert second["cache_hit"] is True
    assert second["value"]["status"] == "FOUND"
