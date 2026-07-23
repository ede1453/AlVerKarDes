from app.domains.events.event_repository_factory import reset_event_repository
from app.domains.profile_aware_recommendations.profile_aware_service import ProfileAwareRecommendationService


async def test_profile_aware_service_generates_recommendations_and_event():
    reset_event_repository()
    service = ProfileAwareRecommendationService()

    result = await service.recommend(
        {
            "user_id": "user-1",
            "query": "MacBook Air",
            "profile_context": {
                "user_id": "user-1",
                "preferred_product_keys": ["macbook-air"],
                "preferred_marketplaces": ["saturn"],
                "preferred_brands": ["Apple"],
                "avoided_product_keys": [],
                "blocked_marketplaces": [],
                "risk_tolerance": "LOW",
                "profile_score": 60,
                "metadata": {"context_version": "user_profile_context_v1"},
            },
            "candidates": [
                {
                    "product_key": "macbook-air",
                    "product_name": "Apple MacBook Air",
                    "marketplace": "saturn",
                    "price": "949.00",
                }
            ],
        }
    )

    assert result["status"] == "COMPLETED"
    assert result["items"][0]["profile_context_applied"] is True

    events = service.event_bus_service.list_recent(
        {"event_type": "profile_aware_recommendation.generated", "source": "profile_aware_recommendations"}
    )
    assert events
