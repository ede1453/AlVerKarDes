from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_rc62_runtime_settings_exposes_cache_backend_without_secrets():
    response = client.get("/api/v1/runtime-settings/status")

    assert response.status_code == 200
    data = response.json()

    assert "settings" in data
    assert data["settings"]["cache_backend"] in {"memory", "redis"}

    response_text = str(data)
    assert "AICI_REDIS_URL" not in response_text
    assert "redis://redis:6379/0" not in response_text
