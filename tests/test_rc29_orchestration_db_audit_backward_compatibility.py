from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_existing_run_with_audit_endpoint_still_uses_existing_contract():
    response = client.post(
        "/api/v1/llm-orchestration/run-with-audit",
        json={
            "preferred_provider": "mock",
            "fallback_providers": [],
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

    assert response.status_code == 200

    data = response.json()
    assert data["orchestration"]["status"] == "COMPLETED"
    assert data["audit_trace"]["assistant_decision"] == "WATCH"
