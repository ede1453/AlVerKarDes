from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_llm_orchestration_vertical_slice_from_prepared_explanation():
    prepared_response = client.post(
        "/api/v1/llm-explanations/prepare",
        json={
            "assistant_decision": "BUY_NOW",
            "headline": "Buy MacBook Air now",
            "summary": "The combined decision supports buying now.",
            "confidence": 94,
            "next_actions": ["Check final seller terms before purchase."],
            "reason_codes": ["ASSISTANT_BUY_SIGNAL"],
            "assistant_context": {
                "product_name": "MacBook Air",
            },
            "prompt_version": "shopping_v1",
        },
    )

    assert prepared_response.status_code == 200
    prepared = prepared_response.json()

    orchestration_response = client.post(
        "/api/v1/llm-orchestration/run",
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

    assert orchestration_response.status_code == 200

    data = orchestration_response.json()

    assert data["status"] == "COMPLETED"
    assert data["selected_provider"] == "mock"
    assert data["fallback_used"] is True
    assert data["prompt_version"] == "shopping_v1"
