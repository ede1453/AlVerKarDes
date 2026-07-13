from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_recommendation_api_does_not_duplicate_api_v1_prefix():
    response = client.get("/openapi.json")
    assert response.status_code == 200

    paths = response.json()["paths"]

    assert "/api/v1/recommendations/evaluate" in paths
    assert "/api/v1/api/v1/recommendations/evaluate" not in paths
