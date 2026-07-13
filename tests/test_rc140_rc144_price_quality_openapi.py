from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

def test_rc140_rc144_routes_registered():
    paths = client.get("/openapi.json").json()["paths"]
    for path in [
        "/api/v1/price-quality/anomaly",
        "/api/v1/price-quality/freshness",
        "/api/v1/price-quality/currency",
        "/api/v1/price-quality/reconcile",
        "/api/v1/price-quality/best-offer",
        "/api/v1/price-quality/pipeline",
    ]:
        assert path in paths
