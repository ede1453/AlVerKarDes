from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_product_matching_vertical_slice_from_unified_search_offers():
    search_response = client.post(
        "/api/v1/unified-search/search",
        json={
            "query": "MacBook Air",
            "offers": [
                {"marketplace": "amazon", "seller": "Amazon", "product_name": "MacBook Air M3 13", "price": "999.00"},
                {"marketplace": "saturn", "seller": "Saturn", "product_name": "MacBook Air M3 13", "price": "949.00"},
            ],
        },
    )
    assert search_response.status_code == 200
    offers = search_response.json()["aggregation"]["offers"]

    match_response = client.post(
        "/api/v1/product-matching/match",
        json={"query": "MacBook Air", "offers": offers},
    )

    assert match_response.status_code == 200
    data = match_response.json()

    assert data["group_count"] == 1
    assert data["matched_offer_count"] == 2
