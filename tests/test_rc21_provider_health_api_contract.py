from fastapi.testclient import TestClient

from app.main import app
from tests.auth_test_helpers import operator_headers


def test_provider_health_check_api_returns_summary():
    with TestClient(app) as client:
        headers = operator_headers(client)
        response = client.post(
            "/api/v1/llm-provider-health/check",
            headers=headers,
            json={
                "providers": ["mock", "openai"],
                "include_external_boundaries": True,
            },
        )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "DEGRADED"
    assert any(item["provider"] == "mock" for item in data["providers"])


def test_provider_health_summary_api_returns_default_summary():
    with TestClient(app) as client:
        headers = operator_headers(client)
        response = client.get("/api/v1/llm-provider-health/summary", headers=headers)

    assert response.status_code == 200
    assert "providers" in response.json()
