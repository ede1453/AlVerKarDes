from app.domains.events.event_repository_factory import reset_event_repository
from app.domains.personalization.personalization_service import PersonalizationService


def test_personalization_service_profile_and_score_emit_events():
    reset_event_repository()
    service = PersonalizationService()

    profile = service.upsert_profile(
        {
            "user_id": "user-1",
            "preferred_marketplaces": ["saturn"],
            "preferred_brands": ["Apple"],
            "max_price": "1000.00",
        }
    )

    assert profile["user_id"] == "user-1"

    result = service.score(
        {
            "user_id": "user-1",
            "offers": [
                {"id": "1", "marketplace": "saturn", "product_name": "Apple MacBook Air", "price": "949.00"},
            ],
        }
    )

    assert result["top_offer"]["marketplace"] == "saturn"

    events = service.event_bus_service.list_recent({"source": "personalization"})
    assert len(events) >= 2


def test_personalization_service_cache_hit_on_second_call():
    service = PersonalizationService()
    service.upsert_profile({"user_id": "user-1", "preferred_marketplaces": ["saturn"]})
    payload = {
        "user_id": "user-1",
        "offers": [{"id": "1", "marketplace": "saturn", "product_name": "MacBook Air", "price": "949.00"}],
        "ttl_seconds": 300,
    }

    first = service.score_cached(payload)
    second = service.score_cached(payload)

    assert first["cache_hit"] is False
    assert second["cache_hit"] is True
