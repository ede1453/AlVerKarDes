"""BILL-001: Subscription tier infrastructure (FREE/PREMIUM), mock
checkout flow (MockPaymentProvider), watchlist quota enforcement, and
notification-threshold PREMIUM-gating. No real payment provider -- see
WIKI_ROOT ADR-016.
"""

from fastapi.testclient import TestClient

from app.main import app
from tests.auth_test_helpers import auth_headers_and_user_id


def test_new_user_defaults_to_free():
    with TestClient(app) as client:
        headers, user_id = auth_headers_and_user_id(client)
        response = client.get(f"/api/v1/billing/subscription/{user_id}", headers=headers)

    assert response.status_code == 200, response.text
    assert response.json()["tier"] == "FREE"


def test_checkout_upgrades_to_premium_and_persists():
    with TestClient(app) as client:
        headers, user_id = auth_headers_and_user_id(client)

        checkout = client.post(
            "/api/v1/billing/checkout",
            headers=headers,
            json={"user_id": user_id, "plan": "PREMIUM"},
        )
        assert checkout.status_code == 200, checkout.text
        assert checkout.json()["tier"] == "PREMIUM"
        assert checkout.json()["provider_reference"].startswith("MOCK-")

        me = client.get(f"/api/v1/billing/subscription/{user_id}", headers=headers)

    assert me.status_code == 200
    assert me.json()["tier"] == "PREMIUM"


def test_cannot_checkout_for_another_user():
    with TestClient(app) as client:
        headers_a, _user_a = auth_headers_and_user_id(client)
        _headers_b, user_b = auth_headers_and_user_id(client)

        attempt = client.post(
            "/api/v1/billing/checkout",
            headers=headers_a,
            json={"user_id": user_b, "plan": "PREMIUM"},
        )

    assert attempt.status_code == 403, attempt.text
    assert attempt.json()["detail"]["code"] == "NOT_RESOURCE_OWNER"


def test_invalid_plan_rejected():
    with TestClient(app) as client:
        headers, user_id = auth_headers_and_user_id(client)

        response = client.post(
            "/api/v1/billing/checkout",
            headers=headers,
            json={"user_id": user_id, "plan": "GOLD"},
        )

    assert response.status_code == 422, response.text


def test_cancel_downgrades_to_free():
    with TestClient(app) as client:
        headers, user_id = auth_headers_and_user_id(client)
        client.post(
            "/api/v1/billing/checkout",
            headers=headers,
            json={"user_id": user_id, "plan": "PREMIUM"},
        )

        cancel = client.post(
            "/api/v1/billing/cancel",
            headers=headers,
            json={"user_id": user_id},
        )

    assert cancel.status_code == 200, cancel.text
    assert cancel.json()["tier"] == "FREE"


def _add_watchlist_item(client: TestClient, headers: dict, user_id: str, n: int):
    return client.post(
        "/api/v1/watchlist/items",
        headers=headers,
        json={
            "user_id": user_id,
            "product_key": f"bill001-product-{n}",
            "query": f"bill001 query {n}",
        },
    )


def test_free_user_blocked_after_watchlist_limit():
    with TestClient(app) as client:
        headers, user_id = auth_headers_and_user_id(client)

        for n in range(10):
            response = _add_watchlist_item(client, headers, user_id, n)
            assert response.status_code == 200, response.text

        eleventh = _add_watchlist_item(client, headers, user_id, 10)

    assert eleventh.status_code == 403, eleventh.text
    assert eleventh.json()["detail"]["code"] == "WATCHLIST_LIMIT_REACHED"
    assert eleventh.json()["detail"]["limit"] == 10


def test_premium_user_not_limited():
    with TestClient(app) as client:
        headers, user_id = auth_headers_and_user_id(client)
        client.post(
            "/api/v1/billing/checkout",
            headers=headers,
            json={"user_id": user_id, "plan": "PREMIUM"},
        )

        for n in range(12):
            response = _add_watchlist_item(client, headers, user_id, n)
            assert response.status_code == 200, response.text


def test_free_user_cannot_customize_threshold():
    with TestClient(app) as client:
        headers, user_id = auth_headers_and_user_id(client)

        response = client.post(
            "/api/v1/deal-notifications/preferences",
            headers=headers,
            json={
                "user_id": user_id,
                "enabled_channels": ["in_app"],
                "minimum_confidence": 55,
                "minimum_discount_pct": 5,
            },
        )

    assert response.status_code == 403, response.text
    assert response.json()["detail"]["code"] == "THRESHOLD_CUSTOMIZATION_REQUIRES_PREMIUM"


def test_free_user_can_still_change_non_threshold_preferences():
    with TestClient(app) as client:
        headers, user_id = auth_headers_and_user_id(client)

        # Echoes the default threshold values back unchanged -- only
        # channels differ from the default. Must be allowed.
        response = client.post(
            "/api/v1/deal-notifications/preferences",
            headers=headers,
            json={
                "user_id": user_id,
                "enabled_channels": ["in_app", "email"],
                "minimum_confidence": 70,
                "minimum_discount_pct": 10,
            },
        )

    assert response.status_code == 200, response.text
    assert response.json()["preferences"]["enabled_channels"] == ["email", "in_app"]


def test_premium_user_can_customize_threshold():
    with TestClient(app) as client:
        headers, user_id = auth_headers_and_user_id(client)
        client.post(
            "/api/v1/billing/checkout",
            headers=headers,
            json={"user_id": user_id, "plan": "PREMIUM"},
        )

        response = client.post(
            "/api/v1/deal-notifications/preferences",
            headers=headers,
            json={
                "user_id": user_id,
                "enabled_channels": ["in_app"],
                "minimum_confidence": 55,
                "minimum_discount_pct": 5,
            },
        )

    assert response.status_code == 200, response.text
    assert response.json()["preferences"]["minimum_confidence"] == 55
