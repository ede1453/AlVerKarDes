from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_rc64_cache_clear_endpoint_still_returns_success():
    response = client.post("/api/v1/cache/clear")

    assert response.status_code == 200
    data = response.json()

    assert data["enabled"] is True
    assert data["backend"] in ["memory", "redis"]
    assert data["entry_count"] == 0
