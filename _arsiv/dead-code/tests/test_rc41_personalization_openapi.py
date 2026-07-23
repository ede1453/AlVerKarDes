from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_personalization_api_registered_in_openapi():
    paths = client.get("/openapi.json").json()["paths"]

    assert "/api/v1/personalization/profiles" in paths
    assert "/api/v1/personalization/profiles/{user_id}" in paths
    assert "/api/v1/personalization/score" in paths
    assert "/api/v1/personalization/score-cached" in paths
    assert "/api/v1/api/v1/personalization/score" not in paths
