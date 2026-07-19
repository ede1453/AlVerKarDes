from fastapi.testclient import TestClient

from app.main import app
from tests.auth_test_helpers import operator_headers


def test_rc64_cache_clear_endpoint_still_returns_success():
    with TestClient(app) as client:
        headers = operator_headers(client)
        response = client.post("/api/v1/cache/clear", headers=headers)

    assert response.status_code == 200
    data = response.json()

    assert data["enabled"] is True
    assert data["backend"] in ["memory", "redis"]
    assert data["entry_count"] == 0
