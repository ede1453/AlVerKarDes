from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_provider_health_check_api_returns_summary():
    response = client.post(
        "/api/v1/llm-provider-health/check",
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
    response = client.get("/api/v1/llm-provider-health/summary")

    assert response.status_code == 200
    assert "providers" in response.json()
