from fastapi.testclient import TestClient

from app.main import app
from tests.auth_test_helpers import internal_service_headers

client = TestClient(app)


def test_crawler_vertical_slice_to_marketplace_aggregation():
    crawl_response = client.post(
        "/api/v1/crawler/crawl",
        json={"url": "https://example.com/product"},
        headers=internal_service_headers(),
    )

    assert crawl_response.status_code == 200
    extracted = crawl_response.json()["extracted"]

    aggregation_response = client.post(
        "/api/v1/marketplace-aggregation/aggregate",
        json={
            "query": "MacBook Air",
            "offers": [
                {
                    "marketplace": "mock_crawler",
                    "seller": "Mock Seller",
                    "product_name": extracted["product_name"],
                    "price": extracted["price"],
                    "currency": extracted["currency"],
                }
            ],
        },
    )

    assert aggregation_response.status_code == 200
    assert aggregation_response.json()["offer_count"] == 1
