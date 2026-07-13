from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_persist_merge_candidate_endpoint_exists_in_openapi():
    response = client.get("/openapi.json")
    assert response.status_code == 200

    paths = response.json()["paths"]

    assert "/api/v1/products/intelligence/merge-candidates/persist" in paths
    assert "post" in paths["/api/v1/products/intelligence/merge-candidates/persist"]
