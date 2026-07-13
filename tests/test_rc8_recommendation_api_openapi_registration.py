from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_recommendation_api_is_registered_in_openapi():
    response = client.get("/openapi.json")
    assert response.status_code == 200

    paths = response.json()["paths"]

    assert "/api/v1/recommendations/evaluate" in paths
    assert "post" in paths["/api/v1/recommendations/evaluate"]
