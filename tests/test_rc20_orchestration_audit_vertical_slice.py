from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_orchestration_audit_vertical_slice_from_prepared_explanation():
    prepared_response = client.post(
        "/api/v1/llm-explanations/prepare",
        json={
            "assistant_decision": "BUY_NOW",
            "headline": "Buy MacBook Air now",
            "summary": "The combined decision supports buying now.",
            "confidence": 94,
            "assistant_context": {"product_name": "MacBook Air"},
            "prompt_version": "shopping_v1",
        },
    )

    assert prepared_response.status_code == 200
    prepared = prepared_response.json()

    response = client.post(
        "/api/v1/llm-orchestration/run-with-audit",
        json={
            "preferred_provider": "openai",
            "fallback_providers": ["mock"],
            "model": "mock-shopping-explainer",
            "system_prompt": prepared["prompt"]["system_prompt"],
            "user_prompt": prepared["prompt"]["user_prompt"],
            "guardrails": prepared["prompt"]["guardrails"],
            "structured_context": prepared["prompt"]["structured_context"],
            "prompt_version": prepared["prompt_version"],
            "max_attempts": 2,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["orchestration"]["fallback_used"] is True
    assert data["audit_trace"]["prompt_version"] == "shopping_v1"
    assert len(data["audit_trace"]["prompt_hash"]) == 64
