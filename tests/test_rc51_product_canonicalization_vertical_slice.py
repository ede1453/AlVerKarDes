from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_product_canonicalization_vertical_slice_from_crawler_to_matching():
    crawl_response = client.post(
        "/api/v1/crawler/crawl",
        json={"url": "https://example.com/product"},
    )
    assert crawl_response.status_code == 200
    extracted = crawl_response.json()["extracted"]

    canonical_response = client.post(
        "/api/v1/product-canonicalization/canonicalize",
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
