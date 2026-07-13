from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_shopping_pipeline_api_registered_in_openapi():
    paths = client.get("/openapi.json").json()["paths"]

    assert "/api/v1/shopping-pipeline/run" in paths
    assert "/api/v1/api/v1/shopping-pipeline/run" not in paths
