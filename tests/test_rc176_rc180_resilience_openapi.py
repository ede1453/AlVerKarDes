from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

def test_rc176_rc180_routes_registered():
    paths = client.get("/openapi.json").json()["paths"]

    for path in [
        "/api/v1/deal-storage-resilience/clear",
        "/api/v1/deal-storage-resilience/outbox",
        "/api/v1/deal-storage-resilience/outbox/claim",
        "/api/v1/deal-storage-resilience/outbox/{event_id}/published",
        "/api/v1/deal-storage-resilience/outbox/{event_id}/failed",
        "/api/v1/deal-storage-resilience/dead-letters/{dead_letter_id}/replay",
        "/api/v1/deal-storage-resilience/backup-exports",
        "/api/v1/deal-storage-resilience/backup-exports/{export_id}",
        "/api/v1/deal-storage-resilience/backup-exports/{export_id}/validate",
        "/api/v1/deal-storage-resilience/health",
        "/api/v1/deal-storage-resilience/health/latest",
    ]:
        assert path in paths
