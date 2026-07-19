from fastapi.testclient import TestClient

from app.main import app
from tests.auth_test_helpers import operator_headers


def test_recommendation_vertical_slice_from_canonical_products():
    with TestClient(app) as client:
        headers = operator_headers(client)

        canonical_response = client.post(
            "/api/v1/product-canonicalization/canonicalize",
            headers=headers,
            json={
                "query": "MacBook Air",
                "offers": [
                    {"id": "1", "marketplace": "amazon", "product_name": "Apple MacBook Air M3 13 inch 512GB", "price": "999.00"},
                    {"id": "2", "marketplace": "saturn", "product_name": "Apple MacBook Air M3 13 inch 512GB", "price": "949.00"},
                ],
            },
        )
        assert canonical_response.status_code == 200
        product = canonical_response.json()["products"][0]

        response = client.post(
            "/api/v1/recommendations/recommend",
            json={
                "query": "MacBook Air",
                "user_id": "user-1",
                "candidates": [
                    {
                        "product_key": product["canonical_key"],
                        "product_name": product["product_name"],
                        "marketplace": "saturn",
                        "price": "949.00",
                        "canonical_confidence": product["confidence"],
                    }
                ],
                "deal_detection": {"deal_level": "EXCELLENT_DEAL"},
                "discount_intelligence": {"discount_quality": "EXCELLENT_REAL_DISCOUNT", "fake_discount_risk": "LOW"},
                "price_prediction": {"recommendation_hint": "BUY_SOON"},
            },
        )

    assert response.status_code == 200
    assert response.json()["items"][0]["rank"] == 1
