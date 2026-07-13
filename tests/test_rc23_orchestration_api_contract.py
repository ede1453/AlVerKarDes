from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_orchestration_api_includes_retry_and_timeout_fields():
    response = client.post(
        "/api/v1/llm-orchestration/run",
        json={
            "preferred_provider": "openai",
            "fallback_providers": ["mock"],
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
            "max_attempts": 2,
            "timeout_ms": 1000,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "COMPLETED"
    assert "retry_decision" in data["attempts"][0]
    assert "timeout_classification" in data["attempts"][0]
