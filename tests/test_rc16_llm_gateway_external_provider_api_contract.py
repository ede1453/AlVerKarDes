from fastapi.testclient import TestClient

from app.main import app
from tests.auth_test_helpers import operator_headers


def test_llm_gateway_api_returns_provider_not_configured_for_openai_by_default():
    with TestClient(app) as client:
        headers = operator_headers(client)
        response = client.post(
            "/api/v1/llm-gateway/generate",
            headers=headers,
            json={
                "provider": "openai",
                "model": "gpt-test",
                "system_prompt": "Explain safely.",
                "user_prompt": "Explain WATCH.",
                "guardrails": ["Do not change assistant_decision."],
                "structured_context": {
                    "assistant_decision": "WATCH",
                    "assistant_context": {
                        "product_name": "Phone",
                    },
                },
            },
        )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "PROVIDER_NOT_CONFIGURED"
    assert data["provider"] == "openai"


def test_llm_gateway_providers_endpoint_lists_available_boundaries():
    with TestClient(app) as client:
        headers = operator_headers(client)
        response = client.get("/api/v1/llm-gateway/providers", headers=headers)

    assert response.status_code == 200

    data = response.json()
    names = {item["name"] for item in data["providers"]}

    assert {"mock", "openai", "local"}.issubset(names)
    assert data["default_provider"] == "mock"
