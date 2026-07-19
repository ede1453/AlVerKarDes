from fastapi.testclient import TestClient

from app.main import app
from tests.auth_test_helpers import auth_headers_and_user_id


def test_shopping_pipeline_vertical_slice_with_profile_store_and_notification():
    with TestClient(app) as client:
        headers, user_id = auth_headers_and_user_id(client)
        client.post("/api/v1/user-profiles/clear", headers=headers)
        client.post(
            "/api/v1/user-profiles/preferences",
            headers=headers,
            json={
                "user_id": user_id,
                "preferred_marketplaces": ["saturn"],
                "preferred_brands": ["Apple"],
                "risk_tolerance": "LOW",
            },
        )

        profile = client.get(
            f"/api/v1/user-profiles/{user_id}/recommendation-context", headers=headers
        )
        assert profile.status_code == 200

        response = client.post(
            "/api/v1/shopping-pipeline/run",
            headers=headers,
            json={
                "user_id": user_id,
                "query": "MacBook Air M3 13 inch 512GB",
                "profile_context": profile.json(),
                "claimed_original_price": "1099.00",
                "deliver_notification": True,
                "channels": ["in_app"],
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
        )

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "COMPLETED"
    assert data["smart_alert"] is not None
    assert data["explanation"] is not None
    assert data["notification"] is not None
