from app.domains.events.event_repository_factory import reset_event_repository
from app.domains.recommendations.recommendation_service import RecommendationService


def test_recommendation_service_emits_event():
    reset_event_repository()
    service = RecommendationService()

    result = service.recommend(
        {
            "query": "MacBook Air",
            "user_id": "user-1",
            "candidates": [
                {"product_key": "macbook-air", "product_name": "MacBook Air", "marketplace": "saturn", "price": "949.00", "canonical_confidence": 95}
            ],
            "deal_detection": {"deal_level": "EXCELLENT_DEAL"},
        }
    )

    assert result["status"] == "COMPLETED"
    assert result["items"]

    events = service.event_bus_service.list_recent({"event_type": "recommendation.generated", "source": "recommendations"})
    assert events


def test_recommendation_service_cache_hit_on_second_call():
    service = RecommendationService()
    payload = {
        "query": "MacBook Air",
        "candidates": [{"product_key": "macbook-air", "product_name": "MacBook Air", "price": "949.00"}],
        "ttl_seconds": 300,
    }

    first = service.recommend_cached(payload)
    second = service.recommend_cached(payload)

    assert first["cache_hit"] is False
    assert second["cache_hit"] is True
