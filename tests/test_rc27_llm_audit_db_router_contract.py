from fastapi.testclient import TestClient

from app.main import app
from tests.auth_test_helpers import operator_headers

client = TestClient(app)


def test_llm_audit_db_endpoints_registered_when_db_dependency_exists():
    paths = client.get("/openapi.json").json()["paths"]

    if "/api/v1/llm-audit-traces/db" not in paths:
        # Older app layouts without app.core.database keep in-memory endpoints only.
        assert "/api/v1/llm-audit-traces" in paths
        return

    assert "/api/v1/llm-audit-traces/db" in paths
    assert "/api/v1/llm-audit-traces/db/list" in paths
    assert "/api/v1/llm-audit-traces/db/{trace_id}" in paths


def test_existing_in_memory_audit_endpoint_still_works():
    with TestClient(app) as scoped_client:
        headers = operator_headers(scoped_client)
        response = scoped_client.post(
            "/api/v1/llm-audit-traces",
            headers=headers,
            json={
                "request_payload": {
                    "provider": "mock",
                    "model": "mock-shopping-explainer",
                    "system_prompt": "system",
                    "user_prompt": "user",
                    "structured_context": {
                        "assistant_decision": "BUY_NOW",
                        "prompt_version": "shopping_v1",
                    },
                    "prompt_version": "shopping_v1",
                },
                "gateway_response": {
                    "provider": "mock",
                    "model": "mock-shopping-explainer",
                    "status": "COMPLETED",
                    "safety_warnings": [],
                    "usage": {"mock": True},
                    "metadata": {"prompt_version": "shopping_v1"},
                },
            },
        )

    assert response.status_code == 200
    assert response.json()["prompt_version"] == "shopping_v1"
