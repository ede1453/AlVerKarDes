from fastapi.testclient import TestClient

from app.main import app
from tests.auth_test_helpers import operator_headers


def test_price_history_vertical_slice_from_product_matching_group():
    with TestClient(app) as client:
        headers = operator_headers(client)
        client.post("/api/v1/price-history/clear", headers=headers)

        match_response = client.post(
            "/api/v1/product-matching/match",
            headers=headers,
            json={
                "query": "MacBook Air",
                "offers": [
                    {"id": "1", "marketplace": "amazon", "product_name": "MacBook Air M3 13", "price": "999.00"},
                    {"id": "2", "marketplace": "saturn", "product_name": "MacBook Air M3 13", "price": "949.00"},
                ],
            },
        )
        assert match_response.status_code == 200
        group = match_response.json()["groups"][0]
        product_key = group["normalized_canonical_name"]

        bulk_response = client.post(
            "/api/v1/price-history/points/bulk",
            headers=headers,
            json={
                "points": [
                    {
                        "product_key": product_key,
                        "marketplace": candidate["marketplace"],
                        "price": candidate["price"],
                        "currency": candidate["currency"],
                    }
                    for candidate in group["candidates"]
                ]
            },
        )

        assert bulk_response.status_code == 200

        summary_response = client.get(
            f"/api/v1/price-history/{product_key}/summary", headers=headers
        )

    assert summary_response.status_code == 200

    summary = summary_response.json()
    assert summary["point_count"] == 2
    assert summary["min_price"] == "949.00"
