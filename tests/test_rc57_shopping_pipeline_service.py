from app.domains.events.event_repository_factory import reset_event_repository
from app.domains.shopping_pipeline.pipeline_service import ShoppingPipelineService


def test_shopping_pipeline_service_runs_end_to_end_and_emits_event():
    reset_event_repository()
    service = ShoppingPipelineService()

    result = service.run(
        {
            "user_id": "user-1",
            "query": "MacBook Air M3 13 inch 512GB",
            "profile_context": {
                "user_id": "user-1",
                "preferred_marketplaces": ["saturn"],
                "preferred_brands": ["Apple"],
                "preferred_product_keys": [],
                "avoided_product_keys": [],
                "blocked_marketplaces": [],
                "risk_tolerance": "LOW",
                "profile_score": 60,
                "metadata": {"context_version": "user_profile_context_v1"},
            },
            "claimed_original_price": "1099.00",
        }
    )

    assert result["status"] == "COMPLETED"
    assert result["top_recommendation"] is not None
    assert result["deal_detection"] is not None
    assert result["discount_intelligence"] is not None
    assert result["explanation"] is not None

    events = service.event_bus_service.list_recent(
        {"event_type": "shopping_pipeline.completed", "source": "shopping_pipeline"}
    )
    assert events


def test_shopping_pipeline_service_can_deliver_notification():
    service = ShoppingPipelineService()

    result = service.run(
        {
            "user_id": "user-1",
            "query": "MacBook Air M3 13 inch 512GB",
            "deliver_notification": True,
            "channels": ["in_app"],
            "claimed_original_price": "1099.00",
        }
    )

    assert result["notification"] is not None
    assert result["notification"]["delivered_count"] >= 0
