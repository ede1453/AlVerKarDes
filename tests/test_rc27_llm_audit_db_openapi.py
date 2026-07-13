from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_llm_audit_db_openapi_has_no_double_prefix():
    paths = client.get("/openapi.json").json()["paths"]

    assert "/api/v1/api/v1/llm-audit-traces/db" not in paths
