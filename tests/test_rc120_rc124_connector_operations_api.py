from fastapi.testclient import TestClient

from app.main import app
from tests.auth_test_helpers import operator_headers

def test_rc120_rc124_vertical_slice():
    with TestClient(app) as client:
        headers = operator_headers(client)
        client.post("/api/v1/connector-operations/clear", headers=headers)

        profile = client.post(
            "/api/v1/connector-operations/credential-profiles",
            headers=headers,
            json={
                "profile_id":"amazon-de-prod",
                "provider":"env",
                "secret_reference":"AICI_AMAZON_DE_CREDENTIALS",
            },
        )
        assert profile.status_code == 200
        assert profile.json()["registered"] is True

        validation = client.post(
            "/api/v1/connector-operations/validate-items",
            headers=headers,
            json={"items":[{
                "external_offer_id":"1",
                "product_title":"Laptop",
                "product_url":"https://x.test",
                "price":999,
                "currency":"EUR",
            }]},
        ).json()
        assert validation["valid"] is True

        retry = client.post(
            "/api/v1/connector-operations/retry",
            headers=headers,
            json={"operation_key":"amazon-run","base_delay_seconds":5},
        ).json()
        assert retry["scheduled"] is True

        schedule = client.post(
            "/api/v1/connector-operations/schedules",
            headers=headers,
            json={
                "schedule_id":"amazon-hourly",
                "source_id":"amazon-de",
                "interval_minutes":60,
            },
        ).json()
        assert schedule["registered"] is True

        client.post(
            "/api/v1/connector-operations/metrics",
            headers=headers,
            json={
                "source_id":"amazon-de",
                "collected_count":10,
                "ingested_count":9,
                "failed_count":1,
                "duration_ms":500,
            },
        )
        metrics = client.get(
            "/api/v1/connector-operations/metrics/amazon-de",
            headers=headers,
        ).json()
    assert metrics["run_count"] == 1
