from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_llm_orchestration_api_runs_with_mock():
    response = client.post(
        "/api/v1/llm-orchestration/run",
        json={
            "preferred_provider": "mock",
            "fallback_providers": [],
            "system_prompt": "Explain safely.",
            "user_prompt": "Explain BUY_NOW.",
            "guardrails": ["Do not change assistant_decision."],
            "structured_context": {
                "assistant_decision": "BUY_NOW",
                "assistant_context": {"product_name": "MacBook Air"},
            },
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "COMPLETED"
    assert data["selected_provider"] == "mock"


def test_llm_orchestration_api_falls_back_to_mock():
    response = client.post(
        "/api/v1/llm-orchestration/run",
        json={
            "preferred_provider": "openai",
            "fallback_providers": ["mock"],
            "system_prompt": "Explain safely.",
            "user_prompt": "Explain BUY_NOW.",
            "guardrails": ["Do not change assistant_decision."],
            "structured_context": {
                "assistant_decision": "BUY_NOW",
                "assistant_context": {"product_name": "MacBook Air"},
            },
            "max_attempts": 2,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "COMPLETED"
    assert data["selected_provider"] == "mock"
    assert data["fallback_used"] is True
