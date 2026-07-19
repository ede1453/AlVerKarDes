from fastapi.testclient import TestClient

from app.main import app
from tests.auth_test_helpers import operator_headers

def test_rc176_rc180_vertical_slice():
    with TestClient(app) as client:
        headers = operator_headers(client)

        client.post(
            "/api/v1/deal-storage-resilience/clear",
            headers=headers,
        )

        event = client.post(
            "/api/v1/deal-storage-resilience/outbox",
            headers=headers,
            json={
                "aggregate_id":"deal-1",
                "event_type":"DEAL_UPDATED",
                "payload":{"status":"VALIDATED"}
            },
        ).json()["event"]

        claimed = client.post(
            "/api/v1/deal-storage-resilience/outbox/claim",
            headers=headers,
        ).json()
        assert claimed["claimed_count"] == 1

        published = client.post(
            f"/api/v1/deal-storage-resilience/outbox/{event['event_id']}/published",
            headers=headers,
        ).json()
        assert published["event"]["status"] == "PUBLISHED"

        export = client.post(
            "/api/v1/deal-storage-resilience/backup-exports",
            headers=headers,
            json={
                "backup_name":"daily",
                "records":[
                    {
                        "deal_id":"deal-1",
                        "payload_hash":"abc"
                    }
                ],
                "manifests":[]
            },
        ).json()["export"]

        validation = client.post(
            f"/api/v1/deal-storage-resilience/backup-exports/{export['export_id']}/validate",
            headers=headers,
            json={"expected_record_count":1},
        ).json()
        assert validation["valid"] is True

        health = client.post(
            "/api/v1/deal-storage-resilience/health",
            headers=headers,
            json={
                "database_reachable":True,
                "pending_outbox_count":0,
                "dead_letter_count":0,
                "last_backup_age_hours":12,
                "integrity_healthy":True
            },
        ).json()
    assert health["sample"]["status"] == "HEALTHY"
