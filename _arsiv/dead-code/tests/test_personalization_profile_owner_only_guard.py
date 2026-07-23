"""VISION-003: extracted from test_auth_003_part2_owner_only_guards.py --
the personalization domain (and its /personalization/profiles endpoint) was
archived (no production caller; ai_shopping_agent, its only real consumer,
was archived in VISION-002). Kept here for historical reference, not part
of the active suite (tests/ is the only pytest testpath).
"""

import uuid

from fastapi.testclient import TestClient

from app.main import app


def _register_and_login(client: TestClient) -> tuple[str, dict[str, str]]:
    email = f"auth003p2_{uuid.uuid4().hex}@example.com"
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


def test_personalization_profile_cross_user_access_is_forbidden():
    with TestClient(app) as client:
        user_a, headers_a = _register_and_login(client)
        _, headers_b = _register_and_login(client)

        upsert = client.post(
            "/api/v1/personalization/profiles",
            headers=headers_a,
            json={"user_id": user_a, "risk_tolerance": "HIGH"},
        )
        assert upsert.status_code == 200, upsert.text

        cross_user_get = client.get(f"/api/v1/personalization/profiles/{user_a}", headers=headers_b)
        cross_user_write = client.post(
            "/api/v1/personalization/profiles",
            headers=headers_b,
            json={"user_id": user_a, "risk_tolerance": "LOW"},
        )
        own_get = client.get(f"/api/v1/personalization/profiles/{user_a}", headers=headers_a)

    assert cross_user_get.status_code == 403, cross_user_get.text
    assert cross_user_write.status_code == 403, cross_user_write.text
    assert own_get.status_code == 200, own_get.text
    assert own_get.json()["risk_tolerance"] == "HIGH"
