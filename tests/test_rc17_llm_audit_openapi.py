from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_llm_audit_api_is_registered_in_openapi():
    response = client.get("/openapi.json")
    assert response.status_code == 200

    paths = response.json()["paths"]

    assert "/api/v1/llm-audit-traces" in paths
    assert "post" in paths["/api/v1/llm-audit-traces"]
    assert "get" in paths["/api/v1/llm-audit-traces"]
    assert "/api/v1/llm-audit-traces/{trace_id}" in paths
    assert "/api/v1/api/v1/llm-audit-traces" not in paths
