"""AUTH-001: record_successful_login()/issue_token_pair() were missing
self.repository.commit(), so a "successful" login never actually persisted
its session/refresh-token row (see ADR-002, AUTH-000 envanteri). Before the
fix: /auth/refresh rejected a token issued moments earlier, and
/auth/sessions always came back empty, even for a session that had just
been created.

Uses `with TestClient(app) as client:` so all requests in a test share one
event loop / one set of pooled DB connections — calling client.post() twice
without the context manager reuses connections across mismatched loops and
fails with an unrelated asyncpg "another operation is in progress" error.
The module-level DB engine (app.core.database.engine) is disposed after
each test for the same reason: its pooled asyncpg connections are bound to
the event loop that created them, and the next test's TestClient opens a
new loop.
"""

import asyncio
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.core.database import engine as db_engine
from app.main import app


@pytest.fixture(autouse=True)
def _dispose_db_engine_after_test():
    yield
    asyncio.run(db_engine.dispose())


def _register_and_login(client: TestClient, email: str) -> dict:
    register = client.post(
        "/api/v1/identity/register",
        json={"email": email, "password": "StrongPass!2345"},
    )
    assert register.status_code == 201, register.text

    login = client.post(
        "/api/v1/auth/login",
        json={"identifier": email, "password": "StrongPass!2345"},
    )
    assert login.status_code == 200, login.text
    return login.json()


def test_fresh_refresh_token_is_actually_usable():
    with TestClient(app) as client:
        pair = _register_and_login(
            client, f"auth001_pytest_refresh_{uuid4().hex}@example.com"
        )

        refresh = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": pair["refresh_token"]},
        )

    assert refresh.status_code == 200, (
        "a refresh token issued moments ago by /auth/login was rejected — "
        f"got {refresh.status_code}: {refresh.text}. This is the exact "
        "regression the missing commit() caused (the refresh row was never "
        "persisted, so rotate_refresh_token's lookup always missed)."
    )


def test_sessions_endpoint_reflects_the_session_just_created():
    with TestClient(app) as client:
        pair = _register_and_login(
            client, f"auth001_pytest_list_{uuid4().hex}@example.com"
        )

        sessions = client.get(
            "/api/v1/auth/sessions",
            headers={
                "Authorization": f"Bearer {pair['access_token']}"
            },
        )

    assert sessions.status_code == 200
    assert sessions.json() != [], (
        "GET /auth/sessions returned an empty list right after a "
        "successful login — the session row was never committed."
    )
