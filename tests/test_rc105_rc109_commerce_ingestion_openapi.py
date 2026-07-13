from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

def test_routes_registered():
    paths = client.get("/openapi.json").json()["paths"]
    for path in [
        "/api/v1/commerce-ingestion/clear",
        "/api/v1/commerce-ingestion/sources",
        "/api/v1/commerce-ingestion/raw-offers",
        "/api/v1/commerce-ingestion/normalize",
        "/api/v1/commerce-ingestion/price-snapshots",
        "/api/v1/commerce-ingestion/runs",
        "/api/v1/commerce-ingestion/runs/{run_id}/complete",
        "/api/v1/commerce-ingestion/sources/{source_id}/health",
    ]:
        assert path in paths
