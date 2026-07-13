from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_personalization_api_profile_and_score():
    client.post("/api/v1/personalization/clear")

    profile_response = client.post(
        "/api/v1/personalization/profiles",
        json={
            "user_id": "user-1",
            "preferred_marketplaces": ["saturn"],
            "preferred_brands": ["Apple"],
            "max_price": "1000.00",
        },
    )

    assert profile_response.status_code == 200

    score_response = client.post(
        "/api/v1/personalization/score",
        json={
            "user_id": "user-1",
            "offers": [
                {"id": "1", "marketplace": "amazon", "product_name": "Apple MacBook Air", "price": "999.00"},
                {"id": "2", "marketplace": "saturn", "product_name": "Apple MacBook Air", "price": "949.00"},
            ],
        },
    )

    assert score_response.status_code == 200
    assert score_response.json()["top_offer"]["marketplace"] == "saturn"


def test_personalization_cached_api_returns_cache_metadata():
    response = client.post(
        "/api/v1/personalization/score-cached",
        json={
            "user_id": "user-1",
            "offers": [
                {"id": "1", "marketplace": "saturn", "product_name": "MacBook Air", "price": "949.00"}
            ],
            "ttl_seconds": 300,
        },
    )

    assert response.status_code == 200
    assert "cache_hit" in response.json()
