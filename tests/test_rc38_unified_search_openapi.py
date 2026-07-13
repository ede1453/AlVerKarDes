from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_unified_search_api_registered_in_openapi():
    paths = client.get("/openapi.json").json()["paths"]

    assert "/api/v1/unified-search/search" in paths
    assert "/api/v1/unified-search/search-cached" in paths
    assert "/api/v1/api/v1/unified-search/search" not in paths
