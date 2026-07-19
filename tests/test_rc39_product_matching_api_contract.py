from fastapi.testclient import TestClient

from app.main import app
from tests.auth_test_helpers import operator_headers


def test_product_matching_api_groups_offers():
    with TestClient(app) as client:
        headers = operator_headers(client)
        response = client.post(
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

    assert response.status_code == 200
    data = response.json()

    assert data["group_count"] == 1
    # CONNECT-003: this endpoint is now backed by the real products/
    # matching_engine (ADR-007 Karar 2), which scores confidence from the
    # real identity engine's field-detection score, not the archived
    # product_matching domain's candidate-count heuristic (which always
    # returned 88 for exactly 2 candidates regardless of what was detected).
    assert data["groups"][0]["match_confidence"] == 55


def test_product_matching_cached_api_returns_cache_metadata():
    with TestClient(app) as client:
        headers = operator_headers(client)
        response = client.post(
            "/api/v1/product-matching/match-cached",
            headers=headers,
            json={
                "query": "MacBook Air",
                "offers": [
                    {"id": "1", "marketplace": "amazon", "product_name": "MacBook Air M3 13", "price": "999.00"},
                ],
                "ttl_seconds": 300,
            },
        )

    assert response.status_code == 200
    assert "cache_hit" in response.json()
