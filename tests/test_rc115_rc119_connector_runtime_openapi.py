from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

def test_rc115_rc119_routes_registered():
    paths = client.get("/openapi.json").json()["paths"]
    for path in [
        "/api/v1/connector-runtime/clear",
        "/api/v1/connector-runtime/execute",
        "/api/v1/connector-runtime/runs/{run_id}",
        "/api/v1/connector-runtime/events",
        "/api/v1/connector-runtime/price-history/{canonical_product_key}",
    ]:
        assert path in paths
