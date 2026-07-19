from fastapi.testclient import TestClient

from app.main import app
from tests.auth_test_helpers import internal_service_headers

client = TestClient(app)

def test_rc110_rc114_vertical_slice():
    client.post("/api/v1/commerce-ingestion-execution/clear", headers=internal_service_headers())
    job = client.post("/api/v1/commerce-ingestion-execution/jobs", json={
        "source_id":"amazon-de","adapter_type":"json","requested_by":"admin"
    }, headers=internal_service_headers()).json()
    result = client.post(
        f"/api/v1/commerce-ingestion-execution/jobs/{job['job_id']}/execute",
        json={"content":'[{"external_offer_id":"1","product_title":"Laptop","product_url":"https://x.test","price":999,"currency":"EUR"}]'},
        headers=internal_service_headers(),
    )
    assert result.status_code == 200
    assert result.json()["executed"] is True
    jobs = client.get("/api/v1/commerce-ingestion-execution/jobs", headers=internal_service_headers()).json()
    assert jobs["job_count"] == 1
