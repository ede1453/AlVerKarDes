from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_guarded_orchestration_vertical_slice_rate_limit_then_audit():
    rate_response = client.post(
        "/api/v1/rate-limits/check",
        json={
            "key": "vertical-guarded-user",
            "scope": "llm_orchestration",
        },
    )
    assert rate_response.status_code == 200
    assert rate_response.json()["allowed"] is True

    guarded_response = client.post(
        "/api/v1/llm-orchestration/run-guarded-with-audit",
        json={
            "rate_limit_key": "vertical-guarded-user-2",
            "rate_limit_scope": "llm_orchestration",
            "preferred_provider": "mock",
            "fallback_providers": [],
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

    assert guarded_response.status_code == 200
    data = guarded_response.json()

    assert data["rate_limit"]["allowed"] is True
    assert data["orchestration"]["status"] == "COMPLETED"
    assert data["audit_trace"]["prompt_version"] == "shopping_v1"
