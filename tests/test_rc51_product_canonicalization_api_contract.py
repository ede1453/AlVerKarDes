from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_product_canonicalization_api_canonicalizes_products():
    response = client.post(
        "/api/v1/product-canonicalization/canonicalize",
        json={
            "query": "MacBook Air",
            "offers": [
                {"id": "1", "product_name": "Apple MacBook Air M3 13 inch 512GB", "marketplace": "amazon"},
                {"id": "2", "product_name": "Apple MacBook Air M3 13 inch 512GB", "marketplace": "saturn"},
            ],
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["canonical_count"] == 1
    assert data["products"][0]["brand"] == "apple"


def test_product_canonicalization_cached_api_returns_cache_metadata():
    response = client.post(
        "/api/v1/product-canonicalization/canonicalize-cached",
        json={
            "query": "MacBook Air",
            "offers": [{"id": "1", "product_name": "Apple MacBook Air M3 13 inch 512GB"}],
            "ttl_seconds": 300,
        },
    )

    assert response.status_code == 200
    assert "cache_hit" in response.json()
