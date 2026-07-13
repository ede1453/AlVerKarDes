from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_product_canonicalization_api_registered_in_openapi():
    paths = client.get("/openapi.json").json()["paths"]

    assert "/api/v1/product-canonicalization/canonicalize" in paths
    assert "/api/v1/product-canonicalization/canonicalize-cached" in paths
    assert "/api/v1/api/v1/product-canonicalization/canonicalize" not in paths
