from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_unified_search_vertical_slice_search_cache_event():
    client.post("/api/v1/events/clear")

    response = client.post(
        "/api/v1/unified-search/search-cached",
        json={
            "query": "MacBook Air",
            "user_id": "user-1",
            "marketplaces": ["amazon", "saturn"],
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
            "ttl_seconds": 300,
        },
    )

    assert response.status_code == 200
    data = response.json()

    assert data["value"]["status"] == "FOUND"
    assert data["value"]["top_offer"]["marketplace"] == "saturn"

    event_response = client.get(
        "/api/v1/events?event_type=unified_search.completed&source=unified_search"
    )

    assert event_response.status_code == 200
    assert event_response.json()["items"]
