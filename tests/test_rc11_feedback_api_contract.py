from fastapi.testclient import TestClient

from app.main import app
from tests.auth_test_helpers import auth_headers, auth_headers_and_user_id


def test_feedback_learning_api_submits_and_gets_feedback():
    with TestClient(app) as client:
        headers = auth_headers(client)
        response = client.post(
            "/api/v1/feedback-learning/feedback",
            headers=headers,
            json={
                "user_id": "user-1",
                "decision_id": "decision-1",
                "feedback_type": "HELPFUL",
                "rating": 5,
            },
        )

        assert response.status_code == 200
        saved = response.json()

        get_response = client.get(
            f"/api/v1/feedback-learning/feedback/{saved['id']}", headers=headers
        )

    assert get_response.status_code == 200
    assert get_response.json()["id"] == saved["id"]


def test_feedback_learning_api_summarizes_user_feedback():
    with TestClient(app) as client:
        headers, user_id = auth_headers_and_user_id(client)
        client.post(
            "/api/v1/feedback-learning/feedback",
            headers=headers,
            json={
                "user_id": user_id,
                "decision_id": "decision-1",
                "feedback_type": "PURCHASED",
                "rating": 5,
            },
        )

        response = client.get(
            f"/api/v1/feedback-learning/users/{user_id}/summary", headers=headers
        )

    assert response.status_code == 200
    assert response.json()["learning_signal"] == "POSITIVE"
