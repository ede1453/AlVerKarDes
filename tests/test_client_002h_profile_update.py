"""CLIENT-002h: PATCH /identity/me -- profile editing (display_name,
preferred_language, preferred_country). No migration needed, the columns
already existed (used since registration). Same OWNER_ONLY shape as
every other CLIENT-002 settings endpoint (user_id in body + ensure_owner).
"""

from fastapi.testclient import TestClient

from app.main import app
from tests.auth_test_helpers import auth_headers_and_user_id


def test_real_profile_update_then_me_reflects_it():
    with TestClient(app) as client:
        headers, user_id = auth_headers_and_user_id(client)

        update = client.patch(
            "/api/v1/identity/me",
            headers=headers,
            json={
                "user_id": user_id,
                "display_name": "Test Kullanici",
                "preferred_language": "de",
                "preferred_country": "at",
            },
        )
        assert update.status_code == 200, update.text
        body = update.json()
        assert body["display_name"] == "Test Kullanici"
        assert body["preferred_language"] == "de"
        assert body["preferred_country"] == "AT"

        me = client.get("/api/v1/identity/me", headers=headers)

    assert me.status_code == 200
    me_body = me.json()
    assert me_body["display_name"] == "Test Kullanici"
    assert me_body["preferred_language"] == "de"
    assert me_body["preferred_country"] == "AT"


def test_cannot_update_another_users_profile():
    with TestClient(app) as client:
        headers_a, _user_a = auth_headers_and_user_id(client)
        headers_b, user_b = auth_headers_and_user_id(client)

        attempt = client.patch(
            "/api/v1/identity/me",
            headers=headers_a,
            json={"user_id": user_b, "display_name": "Hijacked"},
        )

    assert attempt.status_code == 403, attempt.text
    assert attempt.json()["detail"]["code"] == "NOT_RESOURCE_OWNER"


def test_unsupported_locale_is_rejected():
    with TestClient(app) as client:
        headers, user_id = auth_headers_and_user_id(client)

        response = client.patch(
            "/api/v1/identity/me",
            headers=headers,
            json={"user_id": user_id, "preferred_language": "fr"},
        )

    assert response.status_code == 422, response.text


def test_invalid_country_code_is_rejected():
    with TestClient(app) as client:
        headers, user_id = auth_headers_and_user_id(client)

        response = client.patch(
            "/api/v1/identity/me",
            headers=headers,
            json={"user_id": user_id, "preferred_country": "Germany"},
        )

    assert response.status_code == 422, response.text
