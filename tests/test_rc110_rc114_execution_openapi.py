from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

def test_rc110_rc114_routes_registered():
    paths = client.get("/openapi.json").json()["paths"]
    for path in [
        "/api/v1/commerce-ingestion-execution/clear",
        "/api/v1/commerce-ingestion-execution/jobs",
        "/api/v1/commerce-ingestion-execution/jobs/{job_id}/execute",
        "/api/v1/commerce-ingestion-execution/quarantine",
        "/api/v1/commerce-ingestion-execution/quarantine/{quarantine_id}/replay",
    ]:
        assert path in paths
