from fastapi.testclient import TestClient

from app.main import app
from tests.auth_test_helpers import operator_headers


def test_provider_selection_vertical_slice_from_health_to_orchestration():
    with TestClient(app) as client:
        headers = operator_headers(client)

        health_response = client.get(
            "/api/v1/llm-provider-health/summary", headers=headers
        )
        assert health_response.status_code == 200

        selection_response = client.post(
            "/api/v1/llm-provider-selection/select",
            headers=headers,
            json={
                "candidate_providers": ["mock", "openai", "local"],
                "require_available": True,
            },
        )
        assert selection_response.status_code == 200

        selection = selection_response.json()
        assert selection["selected_provider"] == "mock"

        orchestration_response = client.post(
            "/api/v1/llm-orchestration/run-intelligent",
            headers=headers,
            json={
                "candidate_providers": ["mock", "openai", "local"],
                "system_prompt": "Explain safely.",
                "user_prompt": "Explain WATCH.",
                "guardrails": ["Do not change assistant_decision."],
                "structured_context": {
                    "assistant_decision": "WATCH",
                    "assistant_context": {"product_name": "Phone"},
                    "prompt_version": "shopping_v1",
                },
                "prompt_version": "shopping_v1",
            },
        )

    assert orchestration_response.status_code == 200
    assert orchestration_response.json()["orchestration"]["selected_provider"] == "mock"
