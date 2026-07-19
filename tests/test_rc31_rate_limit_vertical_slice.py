from fastapi.testclient import TestClient

from app.main import app
from tests.auth_test_helpers import operator_headers


def test_rate_limit_vertical_slice_before_llm_orchestration():
    with TestClient(app) as client:
        headers = operator_headers(client)
        limit_response = client.post(
            "/api/v1/rate-limits/check",
            headers=headers,
            json={
                "key": "vertical-user",
                "scope": "llm_orchestration",
            },
        )

        assert limit_response.status_code == 200
        assert limit_response.json()["allowed"] is True

        orchestration_response = client.post(
            "/api/v1/llm-orchestration/run",
            headers=headers,
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

    assert orchestration_response.status_code == 200
    assert orchestration_response.json()["status"] == "COMPLETED"
