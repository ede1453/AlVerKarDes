from fastapi.testclient import TestClient

from app.main import app
from tests.auth_test_helpers import operator_headers


def test_guarded_orchestration_api_runs_when_allowed():
    with TestClient(app) as client:
        headers = operator_headers(client)
        response = client.post(
            "/api/v1/llm-orchestration/run-guarded",
            headers=headers,
            json={
                "rate_limit_key": "guarded-api-user",
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

    assert response.status_code == 200
    data = response.json()

    assert data["rate_limit"]["allowed"] is True
    assert data["orchestration"]["status"] == "COMPLETED"


def test_guarded_orchestration_with_audit_api_runs_when_allowed():
    with TestClient(app) as client:
        headers = operator_headers(client)
        response = client.post(
            "/api/v1/llm-orchestration/run-guarded-with-audit",
            headers=headers,
            json={
                "rate_limit_key": "guarded-audit-user",
                "rate_limit_scope": "llm_orchestration",
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

    assert data["rate_limit"]["allowed"] is True
    assert data["orchestration"]["status"] == "COMPLETED"
    assert data["audit_trace"]["assistant_decision"] == "WATCH"
