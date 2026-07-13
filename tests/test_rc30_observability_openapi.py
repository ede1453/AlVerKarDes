from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_observability_api_is_registered_in_openapi():
    paths = client.get("/openapi.json").json()["paths"]

    assert "/api/v1/observability/snapshot" in paths
    assert "get" in paths["/api/v1/observability/snapshot"]
    assert "post" in paths["/api/v1/observability/snapshot"]
    assert "/api/v1/api/v1/observability/snapshot" not in paths
