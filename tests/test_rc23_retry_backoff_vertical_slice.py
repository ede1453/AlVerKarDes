from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_retry_backoff_vertical_slice_openai_to_mock():
    response = client.post(
        "/api/v1/llm-orchestration/run",
        json={
            "preferred_provider": "openai",
            "fallback_providers": ["mock"],
            "system_prompt": "Explain safely.",
            "user_prompt": "Explain WATCH.",
            "guardrails": ["Do not change assistant_decision."],
            "structured_context": {
                "assistant_decision": "WATCH",
                "assistant_context": {"product_name": "Phone"},
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
    assert data["selected_provider"] == "mock"
    assert data["attempts"][0]["retry_decision"]["should_retry"] is True
    assert data["metadata"]["timeout_ms"] == 1000
