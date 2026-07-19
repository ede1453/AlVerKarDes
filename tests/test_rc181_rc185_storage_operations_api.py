from fastapi.testclient import TestClient

from app.main import app
from tests.auth_test_helpers import operator_headers

def test_rc181_rc185_vertical_slice():
    with TestClient(app) as client:
        headers = operator_headers(client)

        client.post(
            "/api/v1/deal-storage-operations/clear",
            headers=headers,
        )

        worker = client.post(
            "/api/v1/deal-storage-operations/worker/run",
            headers=headers,
            json={
                "claimed_events":[
                    {
                        "event_id":"event-1",
                        "aggregate_id":"deal-1",
                        "event_type":"DEAL_UPDATED"
                    }
                ],
                "provider_results":{
                    "event-1":True
                }
            },
        ).json()
        assert worker["run"]["published_count"] == 1

        client.post(
            "/api/v1/deal-storage-operations/backup-schedules",
            headers=headers,
            json={
                "schedule_id":"daily",
                "backup_name_prefix":"aici",
                "interval_hours":24
            },
        )

        backup = client.post(
            "/api/v1/deal-storage-operations/backup-schedules/daily/run",
            headers=headers,
            json={
                "record_count":10,
                "manifest_hash":"abc"
            },
        ).json()
        assert backup["executed"] is True

        dashboard = client.post(
            "/api/v1/deal-storage-operations/health-dashboard",
            headers=headers,
            json={
                "storage_health":{
                    "status":"CRITICAL",
                    "score":30
                },
                "pending_outbox_count":200,
                "dead_letter_count":3,
                "last_backup_age_hours":72,
                "latest_restore_drill_successful":False
            },
        ).json()["dashboard"]

        notifications = client.post(
            "/api/v1/deal-storage-operations/notification-bridge",
            headers=headers,
            json={
                "dashboard":dashboard,
                "recipient_user_ids":["admin-1"]
            },
        ).json()

    assert notifications["notification_count"] == 1
