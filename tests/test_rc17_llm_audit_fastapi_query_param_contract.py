from fastapi.testclient import TestClient

from app.main import app
from tests.auth_test_helpers import operator_headers


def test_llm_audit_trace_list_limit_is_query_parameter():
    with TestClient(app) as client:
        headers = operator_headers(client)
        response = client.get(
            "/api/v1/llm-audit-traces?limit=5",
            headers=headers,
        )

    assert response.status_code == 200
    assert response.json()["limit"] == 5


def test_llm_audit_trace_list_rejects_invalid_limit():
    with TestClient(app) as client:
        headers = operator_headers(client)
        response = client.get(
            "/api/v1/llm-audit-traces?limit=0",
            headers=headers,
        )

    assert response.status_code == 422
