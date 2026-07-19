from fastapi.testclient import TestClient

from app.main import app
from tests.auth_test_helpers import operator_headers


def test_product_canonicalization_api_canonicalizes_products():
    with TestClient(app) as client:
        headers = operator_headers(client)
        response = client.post(
            "/api/v1/product-canonicalization/canonicalize",
            headers=headers,
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
    # CONNECT-003: this endpoint is now backed by the real products/
    # normalization engine (ADR-007 Karar 2), which title-cases detected
    # brands ("Apple"), not the archived product_canonicalization domain's
    # lowercase convention.
    assert data["products"][0]["brand"] == "Apple"


def test_product_canonicalization_cached_api_returns_cache_metadata():
    with TestClient(app) as client:
        headers = operator_headers(client)
        response = client.post(
            "/api/v1/product-canonicalization/canonicalize-cached",
            headers=headers,
            json={
                "query": "MacBook Air",
                "offers": [{"id": "1", "product_name": "Apple MacBook Air M3 13 inch 512GB"}],
                "ttl_seconds": 300,
            },
        )

    assert response.status_code == 200
    assert "cache_hit" in response.json()
