from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_rc60_runtime_settings_status_api():
    response = client.get("/api/v1/runtime-settings/status")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] in {"VALID", "INVALID"}
    assert "settings" in data
    assert "issues" in data
    assert "api_version" in data["settings"]
