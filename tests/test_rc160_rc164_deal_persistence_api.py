from fastapi.testclient import TestClient

from app.main import app
from tests.auth_test_helpers import internal_service_headers

client = TestClient(app)

def test_rc160_rc164_vertical_slice():
    client.post("/api/v1/deal-persistence/clear", headers=internal_service_headers())

    persisted = client.post(
        "/api/v1/deal-persistence/records",
        json={
            "deal_id":"deal-1",
            "payload":{
                "status":"VALIDATED",
                "price":899
            }
        },
        headers=internal_service_headers(),
    )
    assert persisted.status_code == 200
    assert persisted.json()["persisted"] is True

    snapshot = client.post(
        "/api/v1/deal-persistence/records/deal-1/snapshots",
        json={"include_metadata":True},
        headers=internal_service_headers(),
    ).json()["snapshot"]

    checkpoint = client.post(
        "/api/v1/deal-persistence/records/deal-1/checkpoints",
        json={
            "lifecycle_status":"VALIDATED",
            "decision_version":1,
            "event_cursor":3
        },
        headers=internal_service_headers(),
    )
    assert checkpoint.json()["created"] is True

    archived = client.post(
        "/api/v1/deal-persistence/records/deal-1/archive",
        json={
            "reason":"Retention",
            "actor":"system"
        },
        headers=internal_service_headers(),
    )
    assert archived.json()["archived"] is True

    recovered = client.post(
        f"/api/v1/deal-persistence/snapshots/{snapshot['snapshot_id']}/recover",
        json={
            "expected_snapshot_hash":snapshot["snapshot_hash"]
        },
        headers=internal_service_headers(),
    )
    assert recovered.json()["recovered"] is True
