from fastapi.testclient import TestClient

from app.main import app
from tests.auth_test_helpers import internal_service_headers, operator_headers


def test_product_canonicalization_vertical_slice_from_crawler_to_matching():
    with TestClient(app) as client:
        headers = operator_headers(client)

        crawl_response = client.post(
            "/api/v1/crawler/crawl",
            headers=internal_service_headers(),
            json={"url": "https://example.com/product"},
        )
        assert crawl_response.status_code == 200
        extracted = crawl_response.json()["extracted"]

        canonical_response = client.post(
            "/api/v1/product-canonicalization/canonicalize",
            headers=headers,
            json={
                "query": "MacBook Air",
                "offers": [
                    {
                        "id": "crawler-1",
                        "marketplace": "mock_crawler",
                        "product_name": extracted["product_name"],
                        "price": extracted["price"],
                        "currency": extracted["currency"],
                    }
                ],
            },
        )

        assert canonical_response.status_code == 200
        canonical = canonical_response.json()["products"][0]

        matching_response = client.post(
            "/api/v1/product-matching/match",
            headers=headers,
            json={
                "query": "MacBook Air",
                "offers": [
                    {
                        "id": canonical["canonical_id"],
                        "marketplace": "canonical",
                        "product_name": canonical["product_name"],
                        "price": "949.00",
                        "currency": "EUR",
                    }
                ],
            },
        )

    assert matching_response.status_code == 200
    assert matching_response.json()["group_count"] == 1
