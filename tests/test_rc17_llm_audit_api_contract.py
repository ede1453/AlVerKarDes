from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_llm_audit_api_creates_and_reads_trace():
    response = client.post(
        "/api/v1/llm-audit-traces",
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

    get_response = client.get(f"/api/v1/llm-audit-traces/{created['id']}")

    assert get_response.status_code == 200
    assert get_response.json()["id"] == created["id"]


def test_llm_audit_api_lists_recent_traces():
    response = client.get("/api/v1/llm-audit-traces?limit=10")

    assert response.status_code == 200
    assert "items" in response.json()
