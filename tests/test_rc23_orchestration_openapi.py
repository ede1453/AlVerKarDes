from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_orchestration_timeout_field_keeps_openapi_valid():
    response = client.get("/openapi.json")
    assert response.status_code == 200

    paths = response.json()["paths"]

    assert "/api/v1/llm-orchestration/run" in paths
    assert "/api/v1/api/v1/llm-orchestration/run" not in paths
