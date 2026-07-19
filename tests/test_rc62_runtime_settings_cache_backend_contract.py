from fastapi.testclient import TestClient

from app.main import app
from tests.auth_test_helpers import operator_headers


def test_rc62_runtime_settings_exposes_cache_backend_without_secrets():
    with TestClient(app) as client:
        headers = operator_headers(client)
        response = client.get("/api/v1/runtime-settings/status", headers=headers)

    assert response.status_code == 200
    data = response.json()

    assert "settings" in data
    assert data["settings"]["cache_backend"] in {"memory", "redis"}

    response_text = str(data)
    assert "AICI_REDIS_URL" not in response_text
    assert "redis://redis:6379/0" not in response_text
