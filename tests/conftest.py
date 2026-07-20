import os

# TEST-002 (2026-07-20): must be set before ANY `app.*` import below (or in
# any test module) -- app.core.config.settings is a module-level singleton
# instantiated at first import, and pydantic-settings reads real env vars
# ahead of .env file values. This makes bcrypt (used by every
# register/login in the test suite, ~250ms/call in production-safe mode)
# use its cheapest cost factor for tests only -- app/core/security.py holds
# the production-safe default (12), completely unaffected outside pytest.
# Does not touch DATABASE_URL or any other setting: real Postgres is still
# used for every test, this only makes a CPU-bound hashing primitive cheaper.
os.environ.setdefault("BCRYPT_ROUNDS", "4")

import asyncio

import pytest

from app.domains.cache.cache_repository_factory import get_cache_repository


@pytest.fixture(autouse=True)
def clear_cache_between_tests():
    cache = get_cache_repository()

    try:
        cache.clear()
    except Exception:
        pass

    yield

    try:
        cache.clear()
    except Exception:
        pass


@pytest.fixture(autouse=True)
def dispose_db_engine_after_test():
    # Each `with TestClient(app) as client:` block runs its requests on its
    # own anyio portal/event loop. app.core.database.engine's asyncpg pool
    # caches connections bound to whichever loop last used them, so the next
    # test's portal (a different loop) fails with "another operation is in
    # progress" when it reuses a stale pooled connection. Disposing after
    # every test forces a fresh connection on the next test's first query.
    yield
    from app.core.database import engine as db_engine

    try:
        asyncio.run(db_engine.dispose())
    except Exception:
        pass