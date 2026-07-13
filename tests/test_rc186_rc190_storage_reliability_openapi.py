from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

def test_rc186_rc190_routes_registered():
    paths = client.get("/openapi.json").json()["paths"]

    for path in [
        "/api/v1/storage-reliability/clear",
        "/api/v1/storage-reliability/worker-leases",
        "/api/v1/storage-reliability/worker-leases/{worker_id}/heartbeat",
        "/api/v1/storage-reliability/worker-leases/{worker_id}/release",
        "/api/v1/storage-reliability/backups",
        "/api/v1/storage-reliability/backups/retention-evaluate",
        "/api/v1/storage-reliability/restore-approvals",
        "/api/v1/storage-reliability/restore-approvals/{approval_id}/decision",
        "/api/v1/storage-reliability/restore-approvals/{approval_id}/can-execute",
        "/api/v1/storage-reliability/dr-plans",
        "/api/v1/storage-reliability/dr-plans/{plan_id}/tests",
        "/api/v1/storage-reliability/slo-samples",
        "/api/v1/storage-reliability/slo-samples/latest",
    ]:
        assert path in paths
