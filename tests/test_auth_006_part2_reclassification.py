"""AUTH-006 Part 2 (ADR-005): the 22 endpoints AUTH-003 Part 2 left at
AUTHENTICATED-only (no ownership data) were each individually re-decided:
- decision-memory/* (3): repository made genuinely Postgres-backed (it was
  silently in-memory despite migration 0005 creating a real table -- see
  ADR-005), and given real OWNER_ONLY enforcement.
- notification-outbox/snooze: was a stub that never looked anything up;
  fixed to use the repository lookup that already existed.
- 6 "/clear"-style + watch/expire: reclassified permanently to ADMIN_ONLY
  (global operations, not owned by a single user).
- 11 user-value calculators + recommendations/intelligence/evaluate:
  reclassified permanently to AUTHENTICATED (stateless, no user_id anywhere).

This file covers the parts that changed behavior (decision-memory, snooze).
The permanent-reclassification comment changes for the other groups don't
change runtime behavior and are exercised by test_auth_003_part1/part2 guard
tests already.
"""

import uuid

import pytest
from fastapi.testclient import TestClient

from app.main import app
from tests.auth_test_helpers import internal_service_headers


def _register_and_login(client: TestClient) -> tuple[str, dict[str, str]]:
    email = f"auth006p2_{uuid.uuid4().hex}@example.com"
    register = client.post(
        "/api/v1/identity/register",
        json={"email": email, "password": "StrongPass!2345"},
    )
    assert register.status_code == 201, register.text
    user_id = register.json()["id"]

    login = client.post(
        "/api/v1/auth/login",
        json={"identifier": email, "password": "StrongPass!2345"},
    )
    assert login.status_code == 200, login.text
    return user_id, {"Authorization": f"Bearer {login.json()['access_token']}"}


def test_decision_memory_cross_user_access_is_forbidden():
    with TestClient(app) as client:
        user_a, headers_a = _register_and_login(client)
        _, headers_b = _register_and_login(client)

        created = client.post(
            "/api/v1/decision-memory/store",
            headers=headers_a,
            json={"user_id": user_a, "final_decision": "BUY_NOW", "confidence": 90},
        )
        assert created.status_code == 200, created.text
        decision_id = created.json()["id"]

        cross_user_get = client.get(
            f"/api/v1/decision-memory/{decision_id}", headers=headers_b
        )
        cross_user_outcome = client.post(
            f"/api/v1/decision-memory/{decision_id}/outcome",
            headers=headers_b,
            json={"decision_price": "100.00", "future_price": "120.00"},
        )
        own_get = client.get(f"/api/v1/decision-memory/{decision_id}", headers=headers_a)

    assert cross_user_get.status_code == 403, cross_user_get.text
    assert cross_user_get.json()["detail"]["code"] == "NOT_RESOURCE_OWNER"
    assert cross_user_outcome.status_code == 403, cross_user_outcome.text
    assert own_get.status_code == 200, own_get.text


def test_decision_memory_is_really_postgres_backed_not_in_memory():
    """Directly queries the DB to prove the record actually landed in
    Postgres (not just a per-process Python dict) -- the concrete
    regression this fix targets."""
    from sqlalchemy import text

    from app.core.database import engine

    with TestClient(app) as client:
        user_a, headers_a = _register_and_login(client)
        created = client.post(
            "/api/v1/decision-memory/store",
            headers=headers_a,
            json={"user_id": user_a, "final_decision": "WATCH", "confidence": 50},
        )
        assert created.status_code == 200, created.text
        decision_id = created.json()["id"]

    import asyncio

    async def _check_row_exists() -> bool:
        # Dispose first: the engine's pool may hold connections bound to the
        # TestClient portal's now-closed event loop (see
        # tests/conftest.py::dispose_db_engine_after_test for the same
        # issue elsewhere) -- a fresh asyncio.run() here is a different loop.
        await engine.dispose()
        async with engine.connect() as conn:
            result = await conn.execute(
                text("SELECT 1 FROM decision_memory WHERE id = :id"),
                {"id": decision_id},
            )
            return result.first() is not None

    assert asyncio.run(_check_row_exists()) is True


def test_notification_outbox_snooze_cross_user_is_forbidden_and_owner_succeeds():
    with TestClient(app) as client:
        user_a, headers_a = _register_and_login(client)
        _, headers_b = _register_and_login(client)

        enqueued = client.post(
            "/api/v1/notification-outbox/enqueue",
            json={"user_id": user_a, "title": "t", "message": "m"},
            headers=internal_service_headers(),
        )
        assert enqueued.status_code == 200, enqueued.text
        notification_id = enqueued.json()["id"]

        cross_user_snooze = client.post(
            "/api/v1/notification-outbox/snooze",
            headers=headers_b,
            json={"notification_id": notification_id, "until": "2026-08-01T00:00:00Z"},
        )
        missing_snooze = client.post(
            "/api/v1/notification-outbox/snooze",
            headers=headers_a,
            json={"notification_id": str(uuid.uuid4()), "until": "2026-08-01T00:00:00Z"},
        )
        own_snooze = client.post(
            "/api/v1/notification-outbox/snooze",
            headers=headers_a,
            json={"notification_id": notification_id, "until": "2026-08-01T00:00:00Z"},
        )

    assert cross_user_snooze.status_code == 403, cross_user_snooze.text
    assert missing_snooze.status_code == 404, missing_snooze.text
    assert own_snooze.status_code == 200, own_snooze.text
    assert own_snooze.json()["snoozed"] is True
    assert own_snooze.json()["snoozed_until"] == "2026-08-01T00:00:00Z"


@pytest.mark.parametrize(
    "path",
    [
        "/api/v1/deal-notifications/clear",
        "/api/v1/watchlist/clear",
        "/api/v1/personalization/clear",
        "/api/v1/user-activity/clear",
        "/api/v1/user-profiles/clear",
    ],
)
def test_permanently_admin_only_clear_endpoints_require_operator_role(path):
    """Updated for AUTH-006 Part 3: these are real require_role(OPERATOR)
    guards now, not just "any authenticated user". A plain SHOPPER (the
    default role) must get 403; an OPERATOR must get 200."""
    from tests.auth_test_helpers import operator_headers

    with TestClient(app) as client:
        no_token = client.post(path)
        _, shopper_headers = _register_and_login(client)
        as_shopper = client.post(path, headers=shopper_headers)
        as_operator = client.post(path, headers=operator_headers(client))

    assert no_token.status_code == 401, f"{path}: {no_token.text}"
    assert as_shopper.status_code == 403, f"{path}: {as_shopper.text}"
    assert as_operator.status_code == 200, f"{path}: {as_operator.text}"


@pytest.mark.parametrize(
    "path,body",
    [
        ("/api/v1/recommendations/intelligence/evaluate", {"deal_score": 80, "authenticity_score": 80}),
        ("/api/v1/user-value/savings/calculate", {"payload": {"reference_price": 100, "paid_price": 80}}),
    ],
)
def test_permanently_authenticated_calculators_require_only_authentication(path, body):
    with TestClient(app) as client:
        no_token = client.post(path, json=body)
        _, headers = _register_and_login(client)
        with_token = client.post(path, json=body, headers=headers)

    assert no_token.status_code == 401, f"{path}: {no_token.text}"
    assert with_token.status_code == 200, f"{path}: {with_token.text}"
