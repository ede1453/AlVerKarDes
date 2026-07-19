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