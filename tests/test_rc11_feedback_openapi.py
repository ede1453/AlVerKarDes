from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_feedback_learning_api_is_registered_in_openapi():
    response = client.get("/openapi.json")
    assert response.status_code == 200

    paths = response.json()["paths"]

    assert "/api/v1/feedback-learning/feedback" in paths
    assert "/api/v1/feedback-learning/feedback/{feedback_id}" in paths
    assert "/api/v1/feedback-learning/users/{user_id}/summary" in paths
    assert "/api/v1/feedback-learning/decisions/{decision_id}/summary" in paths
    assert "/api/v1/api/v1/feedback-learning/feedback" not in paths
