from fastapi.testclient import TestClient

from app.main import app
from tests.auth_test_helpers import internal_service_headers

client = TestClient(app)


def test_crawler_api_crawls_allowed_mock_boundary():
    response = client.post(
        "/api/v1/crawler/crawl",
        json={"url": "https://example.com/product"},
        headers=internal_service_headers(),
    )

    assert response.status_code == 200
    assert response.json()["status"] == "FETCHED"
    assert response.json()["extracted"]["price"] == "949.00"


def test_crawler_api_blocks_external_fetch_by_default():
    response = client.post(
        "/api/v1/crawler/crawl",
        json={"url": "https://amazon.de/product"},
        headers=internal_service_headers(),
    )

    assert response.status_code == 200
    assert response.json()["status"] == "EXTERNAL_FETCH_DISABLED"
