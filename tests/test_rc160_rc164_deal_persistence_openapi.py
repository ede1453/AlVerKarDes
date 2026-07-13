from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

def test_rc160_rc164_routes_registered():
    paths = client.get("/openapi.json").json()["paths"]
    for path in [
        "/api/v1/deal-persistence/clear",
        "/api/v1/deal-persistence/records",
        "/api/v1/deal-persistence/records/{deal_id}",
        "/api/v1/deal-persistence/records/{deal_id}/snapshots",
        "/api/v1/deal-persistence/snapshots/{snapshot_id}",
        "/api/v1/deal-persistence/records/{deal_id}/checkpoints",
        "/api/v1/deal-persistence/records/{deal_id}/checkpoints/latest",
        "/api/v1/deal-persistence/records/{deal_id}/archive",
        "/api/v1/deal-persistence/archives",
        "/api/v1/deal-persistence/snapshots/{snapshot_id}/recover",
        "/api/v1/deal-persistence/recovery-events",
    ]:
        assert path in paths
