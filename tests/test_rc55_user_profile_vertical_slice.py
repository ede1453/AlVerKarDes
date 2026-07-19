from fastapi.testclient import TestClient

from app.main import app
from tests.auth_test_helpers import auth_headers_and_user_id


def test_user_profile_vertical_slice_from_activity_summary_to_recommendation_context():
    with TestClient(app) as client:
        headers, user_id = auth_headers_and_user_id(client)

        client.post("/api/v1/user-activity/clear", headers=headers)
        client.post("/api/v1/user-profiles/clear", headers=headers)

        client.post(
            "/api/v1/user-activity/record",
            headers=headers,
            json={"user_id": user_id, "event_type": "liked", "product_key": "macbook-air"},
        )

        summary = client.get(
            f"/api/v1/user-activity/users/{user_id}/summary", headers=headers
        )
        assert summary.status_code == 200

        merge = client.post(
            "/api/v1/user-profiles/feedback/merge",
            headers=headers,
            json={"user_id": user_id, "feedback_summary": summary.json()},
        )
        assert merge.status_code == 200

        context = client.get(
            f"/api/v1/user-profiles/{user_id}/recommendation-context", headers=headers
        )

    assert context.status_code == 200
    assert "macbook-air" in context.json()["preferred_product_keys"]
