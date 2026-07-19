"""CONNECT-001 side finding: POST /products/from-name crashed with a plain
500 (ValueError: too many values to unpack) on every call -- the router
unpacked ProductService.create_from_name()'s 3-tuple return
(product, identity, created) into only 2 variables. Found incidentally while
live-verifying CONNECT-001's shopping_pipeline fix (which needed this
endpoint to create a controlled test product). No test previously covered
this endpoint at all."""

import uuid

from fastapi.testclient import TestClient

from app.main import app
from tests.auth_test_helpers import operator_headers


def test_products_from_name_endpoint_creates_product_without_error():
    with TestClient(app) as client:
        headers = operator_headers(client)
        # A name with no recognized brand/family/model collapses to a
        # degenerate canonical_key of just the country code ("de") in the
        # real normalizer -- ProductRepository dedupes on canonical_key, so
        # a generic random-string name would silently hit an unrelated
        # pre-existing "de"-keyed row instead of actually creating this one
        # (discovered while writing this test). "zx<4 digits>" reliably
        # matches the normalizer's fallback model regex ([a-z]{1,4}\d{2,5}),
        # making the canonical_key (and this test) actually unique per run.
        model_token = f"zx{uuid.uuid4().int % 10000:04d}"
        product_name = f"Lenovo ThinkPad {model_token} 256GB"

        response = client.post(
            "/api/v1/products/from-name",
            params={"product_name": product_name, "country": "DE"},
            headers=headers,
        )

    assert response.status_code == 201, response.text
    data = response.json()
    assert data["title"] == product_name
    assert "canonical_key" in data
    assert "identity" in data
