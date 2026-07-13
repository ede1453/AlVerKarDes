from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_crawler_api_registered_in_openapi():
    paths = client.get("/openapi.json").json()["paths"]

    assert "/api/v1/crawler/crawl" in paths
    assert "/api/v1/api/v1/crawler/crawl" not in paths
