"""CLIENT-002f: closes the AUTH-000 finding -- POST /auth/password-reset/confirm
didn't exist (404) and POST /auth/password-reset/issue was a stub that never
looked anything up or sent anything. complete_password_reset()/
issue_purpose_token() already existed in AuthenticationCoreService (single-use
+ expiring token consumption, password policy/history checks, security_version
bump, session revocation) -- they were simply never wired to a route.

Email delivery is captured via a dependency override (get_email_provider),
not by scraping logs -- the LogEmailProvider used in production/dev just logs
instead of sending; these tests never touch it.
"""

import asyncio
import re
import uuid

from fastapi.testclient import TestClient

from app.core.config import settings
from app.domains.email.factory import get_email_provider
from app.main import app


class _CapturingEmailProvider:
    def __init__(self):
        self.sent: list[dict] = []

    async def send(self, *, to: str, subject: str, body: str) -> None:
        self.sent.append({"to": to, "subject": subject, "body": body})


def _extract_token(body: str) -> str:
    match = re.search(r"token=([^\s&]+)", body)
    assert match, f"no token found in email body: {body!r}"
    return match.group(1)


def _register(client: TestClient, *, password: str = "OriginalPass!2345") -> tuple[str, str]:
    email = f"client002f_{uuid.uuid4().hex}@example.com"
    register = client.post(
        "/api/v1/identity/register",
        json={"email": email, "password": password},
    )
    assert register.status_code == 201, register.text
    return email, password


def _expire_password_reset_token(user_email: str) -> None:
    # Same pattern as tests/auth_test_helpers.py::_promote_role -- a
    # throwaway, immediately-disposed engine rather than the shared
    # app.core.database.engine (which is bound to whatever event loop/
    # TestClient portal last used it).
    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import create_async_engine

    async def _do() -> None:
        engine = create_async_engine(settings.DATABASE_URL)
        try:
            async with engine.begin() as conn:
                await conn.execute(
                    text(
                        "UPDATE auth_tokens SET expires_at = NOW() - INTERVAL '1 minute' "
                        "WHERE purpose = 'PASSWORD_RESET' AND consumed_at IS NULL "
                        "AND user_id = (SELECT id FROM users WHERE email = :email)"
                    ),
                    {"email": user_email.lower()},
                )
        finally:
            await engine.dispose()

    asyncio.run(_do())


def test_password_reset_full_flow_then_old_password_rejected():
    capturing = _CapturingEmailProvider()
    app.dependency_overrides[get_email_provider] = lambda: capturing
    try:
        with TestClient(app) as client:
            email, old_password = _register(client)

            issue = client.post("/api/v1/auth/password-reset/issue", json={"identifier": email})
            assert issue.status_code == 200
            assert issue.json() == {"success": True, "message": "PASSWORD_RESET_REQUEST_ACCEPTED"}

            assert len(capturing.sent) == 1
            assert capturing.sent[0]["to"] == email
            token = _extract_token(capturing.sent[0]["body"])

            new_password = "BrandNewPass!7890"
            confirm = client.post(
                "/api/v1/auth/password-reset/confirm",
                json={"token": token, "new_password": new_password},
            )
            assert confirm.status_code == 200
            assert confirm.json() == {"success": True, "message": "PASSWORD_RESET_COMPLETED"}

            old_login = client.post(
                "/api/v1/auth/login",
                json={"identifier": email, "password": old_password},
            )
            new_login = client.post(
                "/api/v1/auth/login",
                json={"identifier": email, "password": new_password},
            )

        assert old_login.status_code == 401, old_login.text
        assert new_login.status_code == 200, new_login.text
    finally:
        app.dependency_overrides.pop(get_email_provider, None)


def test_password_reset_token_is_single_use():
    capturing = _CapturingEmailProvider()
    app.dependency_overrides[get_email_provider] = lambda: capturing
    try:
        with TestClient(app) as client:
            email, _old_password = _register(client)
            client.post("/api/v1/auth/password-reset/issue", json={"identifier": email})
            token = _extract_token(capturing.sent[0]["body"])

            first = client.post(
                "/api/v1/auth/password-reset/confirm",
                json={"token": token, "new_password": "FirstNewPass!123"},
            )
            second = client.post(
                "/api/v1/auth/password-reset/confirm",
                json={"token": token, "new_password": "SecondNewPass!456"},
            )

        assert first.status_code == 200, first.text
        assert second.status_code == 400, second.text
        assert second.json()["detail"] == "TOKEN_ALREADY_USED"
    finally:
        app.dependency_overrides.pop(get_email_provider, None)


def test_password_reset_expired_token_is_rejected():
    capturing = _CapturingEmailProvider()
    app.dependency_overrides[get_email_provider] = lambda: capturing
    try:
        with TestClient(app) as client:
            email, _old_password = _register(client)
            client.post("/api/v1/auth/password-reset/issue", json={"identifier": email})
            token = _extract_token(capturing.sent[0]["body"])

            _expire_password_reset_token(email)

            response = client.post(
                "/api/v1/auth/password-reset/confirm",
                json={"token": token, "new_password": "TooLatePass!123"},
            )

        assert response.status_code == 400, response.text
        assert response.json()["detail"] == "TOKEN_EXPIRED"
    finally:
        app.dependency_overrides.pop(get_email_provider, None)


def test_password_reset_confirm_rejects_garbage_token():
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/auth/password-reset/confirm",
            json={"token": "x" * 40, "new_password": "WhateverPass!123"},
        )

    assert response.status_code == 400, response.text
    assert response.json()["detail"] == "TOKEN_INVALID"


def test_password_reset_issue_is_enumeration_safe():
    capturing = _CapturingEmailProvider()
    app.dependency_overrides[get_email_provider] = lambda: capturing
    try:
        with TestClient(app) as client:
            real_email, _password = _register(client)
            fake_email = f"never_registered_{uuid.uuid4().hex}@example.com"

            real_response = client.post("/api/v1/auth/password-reset/issue", json={"identifier": real_email})
            fake_response = client.post("/api/v1/auth/password-reset/issue", json={"identifier": fake_email})

        assert real_response.status_code == fake_response.status_code == 200
        assert real_response.json() == fake_response.json()
        # The real user actually got a token issued (side effect), the fake
        # identifier did not -- but that difference is invisible in the
        # response, which is the enumeration-safety property being tested.
        assert len(capturing.sent) == 1
        assert capturing.sent[0]["to"] == real_email
    finally:
        app.dependency_overrides.pop(get_email_provider, None)


def test_password_reset_issue_is_rate_limited():
    capturing = _CapturingEmailProvider()
    app.dependency_overrides[get_email_provider] = lambda: capturing
    try:
        with TestClient(app) as client:
            email, _password = _register(client)

            statuses = []
            for _ in range(7):
                response = client.post("/api/v1/auth/password-reset/issue", json={"identifier": email})
                statuses.append(response.status_code)

        assert statuses[:5] == [200] * 5, statuses
        assert 429 in statuses[5:], statuses
    finally:
        app.dependency_overrides.pop(get_email_provider, None)
