from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _paths():
    return client.get("/openapi.json").json()["paths"]


def test_critical_routes_exist_in_openapi():
    paths = _paths()

    expected = [
        "/health",
        "/api/v1/connectors/search",
        "/api/v1/products/merge/apply",
        "/api/v1/products/merge/verify",
        "/api/v1/products/cleanup/orphans",
        "/api/v1/integrity/check",
        "/api/v1/integrity/duplicate-product-regression",
        "/api/v1/system/release-health",
    ]

    missing = [path for path in expected if path not in paths]

    assert missing == []


def test_product_merge_apply_contract():
    schema = _paths()["/api/v1/products/merge/apply"]

    assert "post" in schema
    assert "requestBody" in schema["post"]
    assert "200" in schema["post"]["responses"]


def test_release_health_contract():
    schema = _paths()["/api/v1/system/release-health"]

    assert "get" in schema
    assert "200" in schema["get"]["responses"]


def test_integrity_contracts():
    paths = _paths()

    assert "get" in paths["/api/v1/integrity/check"]
    assert "get" in paths["/api/v1/integrity/duplicate-product-regression"]
