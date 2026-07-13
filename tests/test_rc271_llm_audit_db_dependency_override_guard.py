from fastapi.testclient import TestClient

from app.main import app

try:
    from app.core.database import get_db
except Exception:  # pragma: no cover - older app layouts
    get_db = None


def test_dependency_overrides_are_clean_after_rc27_db_smoke_test():
    if get_db is None:
        return

    assert get_db not in app.dependency_overrides


def test_db_audit_endpoint_does_not_require_real_db_for_openapi():
    client = TestClient(app)
    response = client.get("/openapi.json")

    assert response.status_code == 200
    assert "/api/v1/api/v1/llm-audit-traces/db" not in response.json()["paths"]
