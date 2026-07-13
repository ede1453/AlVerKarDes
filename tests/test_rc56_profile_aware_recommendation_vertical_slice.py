from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_profile_aware_vertical_slice_from_profile_store():
    client.post("/api/v1/user-profiles/clear")

    client.post(
        "/api/v1/user-profiles/preferences",
        json={
            "user_id": "user-1",
            "preferred_marketplaces": ["saturn"],
            "preferred_brands": ["Apple"],
            "risk_tolerance": "LOW",
        },
    )

    client.post(
        "/api/v1/user-profiles/feedback/merge",
        json={
            "user_id": "user-1",
            "feedback_summary": {
                "event_count": 1,
                "preferred_product_keys": ["macbook-air"],
                "avoided_product_keys": [],
            },
        },
    )

    response = client.post(
        "/api/v1/profile-aware-recommendations/recommend",
        json={
            "user_id": "user-1",
            "query": "MacBook Air",
            "candidates": [
                {
                    "product_key": "macbook-air",
                    "product_name": "Apple MacBook Air",
                    "marketplace": "saturn",
                    "price": "949.00",
                }
            ],
        },
    )

    assert response.status_code == 200
    assert response.json()["profile_context"]["preferred_marketplaces"] == ["saturn"]
    assert response.json()["items"][0]["score"] >= 80
