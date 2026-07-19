from fastapi.testclient import TestClient

from app.main import app
from tests.auth_test_helpers import operator_headers


def test_provider_health_vertical_slice_supports_future_routing_decision():
    with TestClient(app) as client:
        headers = operator_headers(client)
        response = client.post(
            "/api/v1/llm-provider-health/check",
            headers=headers,
            json={
                "providers": ["mock", "openai", "local"],
                "include_external_boundaries": True,
            },
        )

    assert response.status_code == 200

    data = response.json()

    healthy_providers = [
        provider["provider"]
        for provider in data["providers"]
        if provider["status"] == "HEALTHY"
    ]

    assert "mock" in healthy_providers
