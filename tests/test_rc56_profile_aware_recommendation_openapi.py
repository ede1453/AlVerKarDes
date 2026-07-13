from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_profile_aware_recommendation_api_registered_in_openapi():
    paths = client.get("/openapi.json").json()["paths"]

    assert "/api/v1/profile-aware-recommendations/recommend" in paths
    assert "/api/v1/api/v1/profile-aware-recommendations/recommend" not in paths
