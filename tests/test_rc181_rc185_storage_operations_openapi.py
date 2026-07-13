from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

def test_rc181_rc185_routes_registered():
    paths = client.get("/openapi.json").json()["paths"]

    for path in [
        "/api/v1/deal-storage-operations/clear",
        "/api/v1/deal-storage-operations/worker/run",
        "/api/v1/deal-storage-operations/worker/runs",
        "/api/v1/deal-storage-operations/backup-schedules",
        "/api/v1/deal-storage-operations/backup-schedules/{schedule_id}/run",
        "/api/v1/deal-storage-operations/restore-drills",
        "/api/v1/deal-storage-operations/health-dashboard",
        "/api/v1/deal-storage-operations/notification-bridge",
        "/api/v1/deal-storage-operations/notifications",
    ]:
        assert path in paths
