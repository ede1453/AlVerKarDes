from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_recommendation_api_registered_in_openapi():
    paths = client.get("/openapi.json").json()["paths"]

    assert "/api/v1/recommendations/recommend" in paths
    assert "/api/v1/recommendations/recommend-cached" in paths
    assert "/api/v1/api/v1/recommendations/recommend" not in paths
