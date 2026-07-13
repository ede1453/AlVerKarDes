from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_cache_api_is_registered_in_openapi():
    paths = client.get("/openapi.json").json()["paths"]

    assert "/api/v1/cache/status" in paths
    assert "/api/v1/cache/set" in paths
    assert "/api/v1/cache/get" in paths
    assert "/api/v1/api/v1/cache/status" not in paths
