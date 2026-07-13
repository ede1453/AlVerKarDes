from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_rc170_rc175_routes_registered():
    paths = client.get("/openapi.json").json()["paths"]

    for path in [
        "/api/v1/deal-storage-sql/records",
        "/api/v1/deal-storage-sql/records/{deal_id}",
        "/api/v1/deal-storage-sql/transactions",
        "/api/v1/deal-storage-sql/outbox/claim",
        "/api/v1/deal-storage-sql/outbox/{event_id}/publish",
        "/api/v1/deal-storage-sql/retention/purge",
        "/api/v1/deal-storage-sql/integrity/audit",
        "/api/v1/deal-storage-sql/backups",
        "/api/v1/deal-storage-sql/backups/{manifest_id}/verify",
    ]:
        assert path in paths
