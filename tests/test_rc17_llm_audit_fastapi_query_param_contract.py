from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_llm_audit_trace_list_limit_is_query_parameter():
    response = client.get("/api/v1/llm-audit-traces?limit=5")

    assert response.status_code == 200
    assert response.json()["limit"] == 5


def test_llm_audit_trace_list_rejects_invalid_limit():
    response = client.get("/api/v1/llm-audit-traces?limit=0")

    assert response.status_code == 422
