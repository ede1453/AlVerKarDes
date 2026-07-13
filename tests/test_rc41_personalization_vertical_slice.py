from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_personalization_vertical_slice_from_unified_search():
    client.post("/api/v1/personalization/clear")

    client.post(
        "/api/v1/personalization/profiles",
        json={
            "user_id": "user-1",
            "preferred_marketplaces": ["saturn"],
            "preferred_brands": ["Apple"],
            "max_price": "1000.00",
        },
    )

    search_response = client.post(
        "/api/v1/unified-search/search",
        json={
            "query": "MacBook Air",
            "user_id": "user-1",
            "offers": [
                {"marketplace": "amazon", "seller": "Amazon", "product_name": "Apple MacBook Air", "price": "999.00"},
                {"marketplace": "saturn", "seller": "Saturn", "product_name": "Apple MacBook Air", "price": "949.00"},
            ],
        },
    )

    assert search_response.status_code == 200
    offers = search_response.json()["aggregation"]["offers"]

    score_response = client.post(
        "/api/v1/personalization/score",
        json={"user_id": "user-1", "offers": offers},
    )

    assert score_response.status_code == 200
    assert score_response.json()["top_offer"]["marketplace"] == "saturn"
