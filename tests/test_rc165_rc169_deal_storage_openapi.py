from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

def test_rc165_rc169_routes_registered():
    paths = client.get("/openapi.json").json()["paths"]
    for path in [
        "/api/v1/deal-storage/clear",
        "/api/v1/deal-storage/records",
        "/api/v1/deal-storage/records/{deal_id}",
        "/api/v1/deal-storage/transactions",
        "/api/v1/deal-storage/outbox",
        "/api/v1/deal-storage/outbox/{event_id}/publish",
        "/api/v1/deal-storage/retention/purge",
        "/api/v1/deal-storage/integrity/audit",
        "/api/v1/deal-storage/backups",
        "/api/v1/deal-storage/backups/{manifest_id}/verify",
    ]:
        assert path in paths
