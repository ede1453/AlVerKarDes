from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_orchestration_run_with_audit_api_returns_trace():
    response = client.post(
        "/api/v1/llm-orchestration/run-with-audit",
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
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["orchestration"]["status"] == "COMPLETED"
    assert data["orchestration"]["selected_provider"] == "mock"
    assert data["audit_trace"]["provider"] == "mock"
    assert data["audit_trace"]["assistant_decision"] == "BUY_NOW"
