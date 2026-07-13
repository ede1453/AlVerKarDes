from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_marketplace_aggregation_api_returns_sorted_offers():
    response = client.post("/api/v1/marketplace-aggregation/aggregate", json={
        "query": "MacBook Air",
        "offers": [
            {"marketplace": "amazon", "seller": "Amazon", "product_name": "MacBook Air M3", "price": "999.00", "currency": "EUR"},
            {"marketplace": "saturn", "seller": "Saturn", "product_name": "MacBook Air M3", "price": "949.00", "currency": "EUR"},
        ],
    })

    assert response.status_code == 200
    data = response.json()
    assert data["offer_count"] == 2
    assert data["offers"][0]["marketplace"] == "saturn"


def test_marketplace_aggregation_cached_api_returns_cache_metadata():
    payload = {
        "query": "MacBook Air",
        "offers": [{"marketplace": "amazon", "seller": "Amazon", "product_name": "MacBook Air M3", "price": "999.00", "currency": "EUR"}],
        "ttl_seconds": 300,
    }
    response = client.post("/api/v1/marketplace-aggregation/aggregate-cached", json=payload)
    assert response.status_code == 200
    assert "cache_hit" in response.json()
