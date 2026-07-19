"""Shared helper for tests exercising endpoints that now require a token
(AUTH-003 Part 1 onward). Registers a fresh throwaway user on the given
TestClient and returns an Authorization header dict.
"""

import uuid

from fastapi.testclient import TestClient

from app.core.config import settings


def internal_service_headers() -> dict[str, str]:
    """AUTH-004: header dict for endpoints gated by
    require_internal_service_key -- reads the live INTERNAL_SERVICE_KEY from
    settings rather than hardcoding it, so it always matches whatever the
    test environment's .env actually has configured."""
    return {"X-Internal-Service-Key": settings.INTERNAL_SERVICE_KEY}


def auth_headers(client: TestClient) -> dict[str, str]:
    headers, _user_id = auth_headers_and_user_id(client)
    return headers


def auth_headers_and_user_id(client: TestClient) -> tuple[dict[str, str], str]:
    """Like auth_headers, but also returns the registered user's id (as a
    string) so tests can populate an owner-checked `user_id` field/path
    param with a value that will actually match the token holder
    (AUTH-003 Part 2 `ensure_owner` checks)."""
    email = f"authtest_{uuid.uuid4().hex}@example.com"
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
    return {"Authorization": f"Bearer {login.json()['access_token']}"}, user_id


def _promote_role(user_id: str, role: str) -> None:
    """AUTH-006 Part 3: there is no role-management endpoint yet (an open
    question in ADR-005), so tests promote a freshly-registered user by
    writing straight to the database -- same as scripts/promote_superadmin.py
    does for real operators. Uses a brand-new, immediately-disposed engine
    rather than the shared app.core.database.engine: that shared engine's
    pool holds connections bound to whatever event loop last used it (the
    TestClient portal), and reusing it from a bare asyncio.run() here is
    exactly the "another operation is in progress" failure mode this test
    suite has hit repeatedly elsewhere. A throwaway engine sidesteps it."""
    import asyncio

    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import create_async_engine

    from app.core.config import settings

    async def _do() -> None:
        engine = create_async_engine(settings.DATABASE_URL)
        try:
            async with engine.begin() as conn:
                await conn.execute(
                    text("UPDATE users SET role = :role WHERE id = :id"),
                    {"role": role, "id": user_id},
                )
        finally:
            await engine.dispose()

    asyncio.run(_do())


def operator_headers(client: TestClient) -> dict[str, str]:
    """Registers a fresh user, promotes them to OPERATOR, and returns an
    Authorization header dict -- for endpoints gated by
    require_role(UserRole.OPERATOR) (AUTH-006 Part 3)."""
    headers, user_id = auth_headers_and_user_id(client)
    _promote_role(user_id, "OPERATOR")
    return headers


def release_manager_headers(client: TestClient) -> dict[str, str]:
    """Same as operator_headers but promotes to RELEASE_MANAGER -- for the
    release-lifecycle endpoints gated by
    require_role(UserRole.RELEASE_MANAGER) (AUTH-006 Part 3)."""
    headers, user_id = auth_headers_and_user_id(client)
    _promote_role(user_id, "RELEASE_MANAGER")
    return headers


def superadmin_headers(client: TestClient) -> dict[str, str]:
    headers, user_id = auth_headers_and_user_id(client)
    _promote_role(user_id, "SUPERADMIN")
    return headers
