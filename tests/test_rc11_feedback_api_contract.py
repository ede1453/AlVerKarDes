from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_feedback_learning_api_submits_and_gets_feedback():
    response = client.post(
        "/api/v1/feedback-learning/feedback",
        json={
            "user_id": "user-1",
            "decision_id": "decision-1",
            "feedback_type": "HELPFUL",
            "rating": 5,
        },
    )

    assert response.status_code == 200
    saved = response.json()

    get_response = client.get(f"/api/v1/feedback-learning/feedback/{saved['id']}")

    assert get_response.status_code == 200
    assert get_response.json()["id"] == saved["id"]


def test_feedback_learning_api_summarizes_user_feedback():
    client.post(
        "/api/v1/feedback-learning/feedback",
        json={
            "user_id": "user-summary-1",
            "decision_id": "decision-1",
            "feedback_type": "PURCHASED",
            "rating": 5,
        },
    )

    response = client.get("/api/v1/feedback-learning/users/user-summary-1/summary")

    assert response.status_code == 200
    assert response.json()["learning_signal"] == "POSITIVE"
