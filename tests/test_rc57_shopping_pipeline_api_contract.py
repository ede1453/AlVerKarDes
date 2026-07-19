from fastapi.testclient import TestClient

from app.main import app
from tests.auth_test_helpers import auth_headers


def test_shopping_pipeline_api_runs_pipeline():
    with TestClient(app) as client:
        headers = auth_headers(client)
        response = client.post(
            "/api/v1/shopping-pipeline/run",
            headers=headers,
            json={
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
        )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "COMPLETED"
    assert data["recommendation"]["items"]
    assert data["explanation"]["headline"]
