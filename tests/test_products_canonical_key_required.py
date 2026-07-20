"""Products: canonical_key is a required field on POST /products/ (found
live: "Test Product AUTH003P2" was created with canonical_key=None,
breaking watchlist/matching for it with a 422 -- ProductCreate.canonical_key
was optional at the schema level with no application-layer fallback, unlike
ProductService.get_or_create_product()/create_from_name() which always
derives one via ProductNormalizationService (CONNECT-005's hash-fallback
guarantee). Fixed by making canonical_key required + non-blank on
ProductCreate, and NOT NULL at the DB level (migration
0021_products_canonical_key_not_null).
"""

from fastapi.testclient import TestClient

from app.main import app
from tests.auth_test_helpers import operator_headers


def test_creating_product_without_canonical_key_is_rejected():
    with TestClient(app) as client:
        headers = operator_headers(client)

        response = client.post(
            "/api/v1/products/",
            headers=headers,
            json={"title": "Regression Guard Product, No Key"},
        )

    assert response.status_code == 422, response.text


def test_creating_product_with_blank_canonical_key_is_rejected():
    with TestClient(app) as client:
        headers = operator_headers(client)

        response = client.post(
            "/api/v1/products/",
            headers=headers,
            json={"title": "Regression Guard Product, Blank Key", "canonical_key": "   "},
        )

    assert response.status_code == 422, response.text


def test_creating_product_with_real_canonical_key_still_succeeds():
    with TestClient(app) as client:
        headers = operator_headers(client)

        response = client.post(
            "/api/v1/products/",
            headers=headers,
            json={
                "title": "Regression Guard Product, Real Key",
                "canonical_key": "regression-guard::real-key::de",
            },
        )

    assert response.status_code == 201, response.text
    assert response.json()["canonical_key"] == "regression-guard::real-key::de"
