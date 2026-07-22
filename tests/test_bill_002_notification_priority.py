"""BILL-002: minimal but real FREE-vs-PREMIUM notification delivery timing
difference. Reuses the existing DealNotificationService/NotificationChannelRouter
pipeline entirely -- no new queue/worker system. PREMIUM notifications are
scheduled for immediate delivery; FREE notifications carry a real
scheduled_delivery_at in the future and are genuinely refused (not just
labeled) by mark_delivered() until that time actually passes. See
WIKI_ROOT ADR-016.
"""

import time
from datetime import datetime, timezone

from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app
from tests.auth_test_helpers import auth_headers_and_user_id


def _deal():
    return {
        "deal_id": "bill-002-deal",
        "canonical_product_key": "bill-002-product",
        "decision": "BUY",
        "confidence_score": 85,
        "observed_discount_pct": 25,
        "freshness_status": "FRESH",
        "anomaly_detected": False,
        "effective_price": 700,
        "source_id": "amazon",
    }


def test_billing_plans_reflects_three_real_enforced_differences():
    with TestClient(app) as client:
        response = client.get("/api/v1/billing/plans")

    assert response.status_code == 200
    plans = {plan["tier"]: plan for plan in response.json()["plans"]}
    assert plans["FREE"]["watchlist_limit"] == settings.FREE_TIER_WATCHLIST_LIMIT
    assert plans["FREE"]["threshold_customization"] is False
    assert plans["FREE"]["instant_notifications"] is False
    assert plans["FREE"]["notification_delay_seconds"] == settings.FREE_TIER_NOTIFICATION_BATCH_DELAY_SECONDS
    assert plans["PREMIUM"]["watchlist_limit"] is None
    assert plans["PREMIUM"]["threshold_customization"] is True
    assert plans["PREMIUM"]["instant_notifications"] is True
    assert plans["PREMIUM"]["notification_delay_seconds"] == 0


def test_premium_notification_is_deliverable_immediately():
    with TestClient(app) as client:
        headers, user_id = auth_headers_and_user_id(client)
        checkout = client.post(
            "/api/v1/billing/checkout", headers=headers, json={"user_id": user_id, "plan": "PREMIUM"}
        )
        assert checkout.status_code == 200, checkout.text

        built = client.post(
            "/api/v1/deal-notifications/build",
            headers=headers,
            json={"user_id": user_id, "at_time": datetime.now(timezone.utc).isoformat(), "deal": _deal()},
        )
        assert built.status_code == 200, built.text
        body = built.json()
        assert body["created"] is True
        notification = body["notification"]
        assert notification["tier"] == "PREMIUM"

        delivered = client.post(
            f"/api/v1/deal-notifications/{notification['notification_id']}/delivered",
            headers=headers,
            json={"channel": notification["immediate_channels"][0]},
        )

    assert delivered.status_code == 200, delivered.text
    assert delivered.json()["updated"] is True


def test_free_notification_blocked_until_real_scheduled_time_then_deliverable():
    original_delay = settings.FREE_TIER_NOTIFICATION_BATCH_DELAY_SECONDS
    settings.FREE_TIER_NOTIFICATION_BATCH_DELAY_SECONDS = 1
    try:
        with TestClient(app) as client:
            headers, user_id = auth_headers_and_user_id(client)  # stays FREE

            built = client.post(
                "/api/v1/deal-notifications/build",
                headers=headers,
                json={"user_id": user_id, "at_time": datetime.now(timezone.utc).isoformat(), "deal": _deal()},
            )
            assert built.status_code == 200, built.text
            body = built.json()
            assert body["created"] is True
            notification = body["notification"]
            assert notification["tier"] == "FREE"
            channel = (notification["immediate_channels"] + notification["deferred_channels"])[0]

            too_early = client.post(
                f"/api/v1/deal-notifications/{notification['notification_id']}/delivered",
                headers=headers,
                json={"channel": channel},
            )
            assert too_early.status_code == 200
            assert too_early.json()["updated"] is False
            assert too_early.json()["reason"] == "NOT_YET_SCHEDULED"

            time.sleep(1.2)

            now_deliverable = client.post(
                f"/api/v1/deal-notifications/{notification['notification_id']}/delivered",
                headers=headers,
                json={"channel": channel},
            )
        assert now_deliverable.status_code == 200
        assert now_deliverable.json()["updated"] is True
    finally:
        settings.FREE_TIER_NOTIFICATION_BATCH_DELAY_SECONDS = original_delay


def test_free_and_premium_scheduled_delivery_timestamps_differ_measurably():
    with TestClient(app) as client:
        headers_free, user_free = auth_headers_and_user_id(client)
        headers_premium, user_premium = auth_headers_and_user_id(client)
        checkout = client.post(
            "/api/v1/billing/checkout",
            headers=headers_premium,
            json={"user_id": user_premium, "plan": "PREMIUM"},
        )
        assert checkout.status_code == 200, checkout.text

        at_time = datetime.now(timezone.utc).isoformat()
        free_built = client.post(
            "/api/v1/deal-notifications/build",
            headers=headers_free,
            json={"user_id": user_free, "at_time": at_time, "deal": _deal()},
        ).json()
        premium_built = client.post(
            "/api/v1/deal-notifications/build",
            headers=headers_premium,
            json={"user_id": user_premium, "at_time": at_time, "deal": _deal()},
        ).json()

    free_scheduled = datetime.fromisoformat(free_built["notification"]["scheduled_delivery_at"])
    premium_scheduled = datetime.fromisoformat(premium_built["notification"]["scheduled_delivery_at"])
    delta_seconds = (free_scheduled - premium_scheduled).total_seconds()

    # Real timestamp comparison, not a representative/mock value -- FREE's
    # scheduled time must be at least the configured batch delay later than
    # PREMIUM's (small tolerance for the few ms between the two real HTTP
    # calls above).
    assert delta_seconds >= settings.FREE_TIER_NOTIFICATION_BATCH_DELAY_SECONDS - 1
