from fastapi.testclient import TestClient

from app.main import app
from tests.auth_test_helpers import internal_service_headers

client = TestClient(app)

def test_rc165_rc169_vertical_slice():
    client.post("/api/v1/deal-storage/clear", headers=internal_service_headers())

    transaction = client.post(
        "/api/v1/deal-storage/transactions",
        json={
            "deal_id":"deal-1",
            "payload":{"status":"RECOMMENDED"},
            "version":1,
            "event_type":"DEAL_RECOMMENDED",
            "event_payload":{"decision":"BUY"}
        },
        headers=internal_service_headers(),
    )
    assert transaction.status_code == 200
    assert transaction.json()["committed"] is True

    audit = client.post(
        "/api/v1/deal-storage/integrity/audit",
        headers=internal_service_headers(),
    ).json()
    assert audit["healthy"] is True

    manifest = client.post(
        "/api/v1/deal-storage/backups",
        json={"backup_name":"daily"},
        headers=internal_service_headers(),
    ).json()

    verified = client.post(
        f"/api/v1/deal-storage/backups/{manifest['manifest_id']}/verify",
        headers=internal_service_headers(),
    ).json()
    assert verified["verified"] is True
