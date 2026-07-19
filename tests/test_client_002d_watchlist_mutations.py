"""CLIENT-002d: watchlist add/remove wired into the frontend. The
ownership guard itself (ensure_owner) was already built and cross-user
tested in AUTH-003 Part 2 (tests/test_auth_003_part2_owner_only_guards.py::
test_watchlist_item_cross_user_access_is_forbidden covers cross-user
GET/deactivate on an existing item) -- these tests add the two attack
vectors that test didn't cover: impersonating another user's user_id at
CREATE time, and listing another user's items directly.
"""

import uuid

from fastapi.testclient import TestClient

from app.main import app
from tests.auth_test_helpers import auth_headers_and_user_id


def test_cannot_create_watchlist_item_under_another_users_user_id():
    with TestClient(app) as client:
        headers_a, _user_a = auth_headers_and_user_id(client)
        headers_b, user_b = auth_headers_and_user_id(client)

        # A tries to create an item claiming to be B.
        attempt = client.post(
            "/api/v1/watchlist/items",
            headers=headers_a,
            json={"user_id": user_b, "product_key": "p1", "query": "laptop"},
        )

    assert attempt.status_code == 403, attempt.text
    assert attempt.json()["detail"]["code"] == "NOT_RESOURCE_OWNER"


def test_cannot_list_another_users_watchlist():
    with TestClient(app) as client:
        headers_a, user_a = auth_headers_and_user_id(client)
        headers_b, _user_b = auth_headers_and_user_id(client)

        client.post(
            "/api/v1/watchlist/items",
            headers=headers_a,
            json={"user_id": user_a, "product_key": "p1", "query": "laptop"},
        )

        cross_user_list = client.get(f"/api/v1/watchlist/users/{user_a}/items", headers=headers_b)
        own_list = client.get(f"/api/v1/watchlist/users/{user_a}/items", headers=headers_a)

    assert cross_user_list.status_code == 403, cross_user_list.text
    assert own_list.status_code == 200, own_list.text


def test_real_add_then_deactivate_reflects_in_own_list():
    with TestClient(app) as client:
        headers, user_id = auth_headers_and_user_id(client)
        product_key = f"client-002d-watchlist::{uuid.uuid4().hex[:8]}"

        add = client.post(
            "/api/v1/watchlist/items",
            headers=headers,
            json={"user_id": user_id, "product_key": product_key, "query": "CLIENT-002d watchlist test"},
        )
        assert add.status_code == 200, add.text
        item_id = add.json()["id"]
        assert add.json()["status"] == "ACTIVE"

        listing = client.get(f"/api/v1/watchlist/users/{user_id}/items", headers=headers)
        assert listing.status_code == 200
        assert any(item["id"] == item_id and item["product_key"] == product_key for item in listing.json()["items"])

        deactivate = client.post(f"/api/v1/watchlist/items/{item_id}/deactivate", headers=headers)
        assert deactivate.status_code == 200
        assert deactivate.json()["status"] == "INACTIVE"
