from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_rate_limit_api_is_registered_in_openapi():
    paths = client.get("/openapi.json").json()["paths"]

    assert "/api/v1/rate-limits/check" in paths
    assert "/api/v1/api/v1/rate-limits/check" not in paths
