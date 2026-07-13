from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_crawler_api_crawls_allowed_mock_boundary():
    response = client.post(
        "/api/v1/crawler/crawl",
        json={"url": "https://example.com/product"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "FETCHED"
    assert response.json()["extracted"]["price"] == "949.00"


def test_crawler_api_blocks_external_fetch_by_default():
    response = client.post(
        "/api/v1/crawler/crawl",
        json={"url": "https://amazon.de/product"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "EXTERNAL_FETCH_DISABLED"
