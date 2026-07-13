from app.domains.ai_shopping_agent.agent_service import AIShoppingAgentService
from app.domains.events.event_repository_factory import reset_event_repository


def test_ai_shopping_agent_service_runs_full_decision_and_emits_event():
    reset_event_repository()
    service = AIShoppingAgentService()

    result = service.run(
        {
            "query": "MacBook Air",
            "user_id": "user-1",
            "profile": {
                "preferred_marketplaces": ["saturn"],
                "preferred_brands": ["Apple"],
                "max_price": "1000.00",
            },
            "offers": [
                {"id": "1", "marketplace": "amazon", "seller": "Amazon", "product_name": "Apple MacBook Air M3", "price": "999.00"},
                {"id": "2", "marketplace": "saturn", "seller": "Saturn", "product_name": "Apple MacBook Air M3", "price": "949.00"},
            ],
        }
    )

    assert result["decision"] == "BUY_NOW"
    assert result["top_offer"]["marketplace"] == "saturn"
    assert result["search"]["status"] == "FOUND"
    assert result["matching"]["group_count"] == 1
    assert result["price_history"]["point_count"] == 2

    events = service.event_bus_service.list_recent(
        {"event_type": "ai_shopping_agent.completed", "source": "ai_shopping_agent"}
    )
    assert events


def test_ai_shopping_agent_service_cache_hit_on_second_call():
    service = AIShoppingAgentService()
    payload = {
        "query": "MacBook Air",
        "offers": [
            {"id": "1", "marketplace": "amazon", "product_name": "MacBook Air M3", "price": "999.00"},
        ],
        "ttl_seconds": 300,
    }

    first = service.run_cached(payload)
    second = service.run_cached(payload)

    assert first["cache_hit"] is False
    assert second["cache_hit"] is True
