from fastapi.testclient import TestClient

from app.main import app
from tests.auth_test_helpers import operator_headers


def test_intelligent_orchestration_api_runs_with_selected_provider():
    with TestClient(app) as client:
        headers = operator_headers(client)
        response = client.post(
            "/api/v1/llm-orchestration/run-intelligent",
            headers=headers,
            json={
                "candidate_providers": ["mock", "openai", "local"],
                "model": "mock-shopping-explainer",
                "system_prompt": "Explain safely.",
                "user_prompt": "Explain BUY_NOW.",
                "guardrails": ["Do not change assistant_decision."],
                "structured_context": {
                    "assistant_decision": "BUY_NOW",
                    "assistant_context": {"product_name": "MacBook Air"},
                    "prompt_version": "shopping_v1",
                },
                "prompt_version": "shopping_v1",
            },
        )

    assert response.status_code == 200

    data = response.json()

    assert data["selection"]["selected_provider"] == "mock"
    assert data["orchestration"]["status"] == "COMPLETED"
