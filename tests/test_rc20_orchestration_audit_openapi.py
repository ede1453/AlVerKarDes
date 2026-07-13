from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_orchestration_run_with_audit_endpoint_is_registered_in_openapi():
    response = client.get("/openapi.json")
    assert response.status_code == 200

    paths = response.json()["paths"]

    assert "/api/v1/llm-orchestration/run-with-audit" in paths
    assert "post" in paths["/api/v1/llm-orchestration/run-with-audit"]
    assert "/api/v1/api/v1/llm-orchestration/run-with-audit" not in paths
