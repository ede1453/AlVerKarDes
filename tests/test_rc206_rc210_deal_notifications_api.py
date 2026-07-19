from fastapi.testclient import TestClient

from app.main import app
from tests.auth_test_helpers import auth_headers_and_user_id


def test_rc206_rc210_vertical_slice():
    with TestClient(app) as client:
        headers, user_id = auth_headers_and_user_id(client)

        client.post(
            "/api/v1/deal-notifications/clear",
            headers=headers,
        )

        client.post(
            "/api/v1/deal-notifications/preferences",
            headers=headers,
            json={
                "user_id": user_id,
                "enabled_channels": ["push", "in_app"],
                "minimum_confidence": 70,
                "minimum_discount_pct": 20,
                "quiet_hours_enabled": False,
            },
        )

        created = client.post(
            "/api/v1/deal-notifications/build",
            headers=headers,
            json={
                "user_id": user_id,
                "at_time": "2026-07-12T12:00:00+03:00",
                "deal": {
                    "deal_id": "deal-1",
                    "canonical_product_key": "product-1",
                    "decision": "BUY",
                    "confidence_score": 85,
                    "observed_discount_pct": 25,
                    "freshness_status": "FRESH",
                    "anomaly_detected": False,
                    "effective_price": 700,
                    "source_id": "amazon",
                },
            },
        ).json()

        assert created["created"] is True

        notification_id = created["notification"]["notification_id"]

        delivered = client.post(
            f"/api/v1/deal-notifications/{notification_id}/delivered",
            headers=headers,
            json={"channel": "push"},
        ).json()

    assert delivered["notification"]["status"] == "DELIVERED"
