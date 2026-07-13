from app.domains.events.event_repository_factory import reset_event_repository
from app.domains.product_canonicalization.canonical_service import ProductCanonicalizationService


def test_canonicalization_service_emits_event():
    reset_event_repository()
    service = ProductCanonicalizationService()

    result = service.canonicalize(
        {
            "query": "MacBook Air",
            "offers": [
                {"id": "1", "product_name": "Apple MacBook Air M3 13 inch 512GB"},
            ],
        }
    )

    assert result["canonical_count"] == 1

    events = service.event_bus_service.list_recent(
        {"event_type": "product_canonicalization.completed", "source": "product_canonicalization"}
    )
    assert events


def test_canonicalization_service_cache_hit_on_second_call():
    service = ProductCanonicalizationService()
    payload = {
        "query": "MacBook Air",
        "offers": [{"id": "1", "product_name": "Apple MacBook Air M3 13 inch 512GB"}],
        "ttl_seconds": 300,
    }

    first = service.canonicalize_cached(payload)
    second = service.canonicalize_cached(payload)

    assert first["cache_hit"] is False
    assert second["cache_hit"] is True
