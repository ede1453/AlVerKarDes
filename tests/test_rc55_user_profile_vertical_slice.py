from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_user_profile_vertical_slice_from_activity_summary_to_recommendation_context():
    client.post("/api/v1/user-activity/clear")
    client.post("/api/v1/user-profiles/clear")

    client.post(
        "/api/v1/user-activity/record",
        json={"user_id": "user-1", "event_type": "liked", "product_key": "macbook-air"},
    )

    summary = client.get("/api/v1/user-activity/users/user-1/summary")
    assert summary.status_code == 200

    merge = client.post(
        "/api/v1/user-profiles/feedback/merge",
        json={"user_id": "user-1", "feedback_summary": summary.json()},
    )
    assert merge.status_code == 200

    context = client.get("/api/v1/user-profiles/user-1/recommendation-context")
    assert context.status_code == 200
    assert "macbook-air" in context.json()["preferred_product_keys"]
