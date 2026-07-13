from fastapi.testclient import TestClient

from app.main import app

try:
    from app.core.database import get_db
except Exception:  # pragma: no cover
    get_db = None


client = TestClient(app)


def test_orchestration_db_audit_endpoint_registered_when_db_dependency_exists():
    paths = client.get("/openapi.json").json()["paths"]

    if get_db is None:
        assert "/api/v1/llm-orchestration/run-with-audit" in paths
        return

    assert "/api/v1/llm-orchestration/run-with-db-audit" in paths
    assert "/api/v1/api/v1/llm-orchestration/run-with-db-audit" not in paths
