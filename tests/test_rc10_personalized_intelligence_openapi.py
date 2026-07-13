from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_personalized_intelligence_api_is_registered_in_openapi():
    response = client.get("/openapi.json")
    assert response.status_code == 200

    paths = response.json()["paths"]

    assert "/api/v1/personalized-intelligence/profiles" in paths
    assert "/api/v1/personalized-intelligence/profiles/{user_id}" in paths
    assert "/api/v1/personalized-intelligence/decisions/personalize" in paths
    assert "/api/v1/api/v1/personalized-intelligence/profiles" not in paths
