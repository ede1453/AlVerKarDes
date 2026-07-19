from fastapi.testclient import TestClient

from app.main import app
from tests.auth_test_helpers import operator_headers


def test_llm_audit_api_creates_and_reads_trace():
    with TestClient(app) as client:
        headers = operator_headers(client)

        response = client.post(
            "/api/v1/llm-audit-traces",
            headers=headers,
            json={
                "request_payload": {
                    "provider": "mock",
                    "model": "mock-shopping-explainer",
                    "system_prompt": "system",
                    "user_prompt": "user",
                    "structured_context": {"assistant_decision": "WATCH"},
                },
                "gateway_response": {
                    "provider": "mock",
                    "model": "mock-shopping-explainer",
                    "status": "COMPLETED",
                    "safety_warnings": [],
                    "usage": {"mock": True},
                    "metadata": {"deterministic": True},
                },
            },
        )

        assert response.status_code == 200
        created = response.json()

        get_response = client.get(
            f"/api/v1/llm-audit-traces/{created['id']}",
            headers=headers,
        )

    assert get_response.status_code == 200
    assert get_response.json()["id"] == created["id"]


def test_llm_audit_api_lists_recent_traces():
    with TestClient(app) as client:
        headers = operator_headers(client)
        response = client.get(
            "/api/v1/llm-audit-traces?limit=10",
            headers=headers,
        )

    assert response.status_code == 200
    assert "items" in response.json()
