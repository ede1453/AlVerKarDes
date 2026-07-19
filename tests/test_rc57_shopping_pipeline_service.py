import pytest

from app.core.database import AsyncSessionLocal
from app.domains.events.event_repository_factory import reset_event_repository
from app.domains.shopping_pipeline.pipeline_service import ShoppingPipelineService


@pytest.mark.asyncio
async def test_shopping_pipeline_service_runs_end_to_end_and_emits_event():
    reset_event_repository()
    service = ShoppingPipelineService()

    async with AsyncSessionLocal() as db:
        result = await service.run(
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
            },
            db,
        )

    assert result["status"] == "COMPLETED"
    assert result["top_recommendation"] is not None
    # CONNECT-001: price_history is now a real market.Price-backed read (or
    # an honest INSUFFICIENT_DATA, never fabricated). This shared dev DB can
    # legitimately already hold real history for this product name from
    # other tests/sessions, so only the shape/status is asserted here --
    # the OK-vs-INSUFFICIENT_DATA behavior itself is covered deterministically
    # by test_connect_001_shopping_pipeline_price_history.py.
    assert result["price_history"]["status"] in ("OK", "INSUFFICIENT_DATA")
    assert result["deal_detection"] is not None
    assert result["discount_intelligence"] is not None
    assert result["explanation"] is not None

    events = service.event_bus_service.list_recent(
        {"event_type": "shopping_pipeline.completed", "source": "shopping_pipeline"}
    )
    assert events


@pytest.mark.asyncio
async def test_shopping_pipeline_service_can_deliver_notification():
    service = ShoppingPipelineService()

    async with AsyncSessionLocal() as db:
        result = await service.run(
            {
                "user_id": "user-1",
                "query": "MacBook Air M3 13 inch 512GB",
                "deliver_notification": True,
                "channels": ["in_app"],
                "claimed_original_price": "1099.00",
                # CONNECT-001: explicit price_history so this test can
                # exercise the notification-delivery path (should_alert=True)
                # deterministically, without relying on production's old
                # fabricate-from-search-offers behavior (removed).
                "price_history": {
                    "latest_price": "949.00",
                    "min_price": "949.00",
                    "average_price": "974.00",
                    "max_price": "999.00",
                    "trend": "DOWN",
                    "points": [{"price": "949.00"}, {"price": "999.00"}],
                },
            },
            db,
        )

    assert result["notification"] is not None
    assert result["notification"]["delivered_count"] >= 0
