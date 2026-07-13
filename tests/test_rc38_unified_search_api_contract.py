from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_unified_search_api_returns_search_result():
    response = client.post(
        "/api/v1/unified-search/search",
        json={
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
        },
    )

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "FOUND"
    assert data["top_offer"]["marketplace"] == "saturn"
    assert data["candidate_count"] == 2


def test_unified_search_cached_api_returns_cache_metadata():
    payload = {
        "query": "MacBook Air",
        "offers": [
            {
                "marketplace": "amazon",
                "seller": "Amazon",
                "product_name": "MacBook Air M3",
                "price": "999.00",
                "currency": "EUR",
            }
        ],
        "ttl_seconds": 300,
    }

    response = client.post("/api/v1/unified-search/search-cached", json=payload)

    assert response.status_code == 200
    assert "cache_hit" in response.json()
