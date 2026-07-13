from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_ai_shopping_agent_api_runs_decision():
    response = client.post(
        "/api/v1/ai-shopping-agent/run",
        json={
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
        },
    )

    assert response.status_code == 200
    data = response.json()

    assert data["decision"] == "BUY_NOW"
    assert data["top_offer"]["marketplace"] == "saturn"


def test_ai_shopping_agent_cached_api_returns_cache_metadata():
    response = client.post(
        "/api/v1/ai-shopping-agent/run-cached",
        json={
            "query": "MacBook Air",
            "offers": [
                {"id": "1", "marketplace": "amazon", "product_name": "MacBook Air M3", "price": "999.00"},
            ],
            "ttl_seconds": 300,
        },
    )

    assert response.status_code == 200
    assert "cache_hit" in response.json()
