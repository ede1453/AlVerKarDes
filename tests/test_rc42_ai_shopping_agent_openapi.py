from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_ai_shopping_agent_api_registered_in_openapi():
    paths = client.get("/openapi.json").json()["paths"]

    assert "/api/v1/ai-shopping-agent/run" in paths
    assert "/api/v1/ai-shopping-agent/run-cached" in paths
    assert "/api/v1/api/v1/ai-shopping-agent/run" not in paths
