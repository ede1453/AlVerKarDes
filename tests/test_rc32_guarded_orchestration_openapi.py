from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_guarded_orchestration_endpoints_are_registered_in_openapi():
    paths = client.get("/openapi.json").json()["paths"]

    assert "/api/v1/llm-orchestration/run-guarded" in paths
    assert "/api/v1/llm-orchestration/run-guarded-with-audit" in paths
    assert "/api/v1/api/v1/llm-orchestration/run-guarded" not in paths
