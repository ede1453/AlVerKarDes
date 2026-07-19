from fastapi.testclient import TestClient

from app.main import app
from tests.auth_test_helpers import operator_headers


def test_rc60_runtime_settings_status_api():
    with TestClient(app) as client:
        headers = operator_headers(client)
        response = client.get("/api/v1/runtime-settings/status", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert data["status"] in {"VALID", "INVALID"}
    assert "settings" in data
    assert "issues" in data
    assert "api_version" in data["settings"]
