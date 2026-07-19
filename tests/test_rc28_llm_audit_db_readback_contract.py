from fastapi.testclient import TestClient

from app.main import app
from tests.auth_test_helpers import operator_headers

try:
    from app.core.database import get_db
except Exception:  # pragma: no cover
    get_db = None


client = TestClient(app)


def test_db_audit_readback_endpoint_is_registered_when_available():
    paths = client.get("/openapi.json").json()["paths"]

    if get_db is None:
        assert "/api/v1/llm-audit-traces" in paths
        return

    assert "/api/v1/llm-audit-traces/db" in paths
    assert "/api/v1/llm-audit-traces/db/list" in paths
    assert "/api/v1/llm-audit-traces/db/{trace_id}" in paths


def test_in_memory_audit_readback_still_works():
    with TestClient(app) as scoped_client:
        headers = operator_headers(scoped_client)
        create_response = scoped_client.post(
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

        assert create_response.status_code == 200
        created = create_response.json()

        get_response = scoped_client.get(
            f"/api/v1/llm-audit-traces/{created['id']}", headers=headers
        )

        assert get_response.status_code == 200
        assert get_response.json()["id"] == created["id"]

        list_response = scoped_client.get(
            "/api/v1/llm-audit-traces?limit=5", headers=headers
        )

    assert list_response.status_code == 200
    assert any(item["id"] == created["id"] for item in list_response.json()["items"])
