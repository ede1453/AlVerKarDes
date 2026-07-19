import pytest
from sqlalchemy.ext.asyncio import create_async_engine

from app.main import _check_database_reachable, _check_redis_reachable


@pytest.mark.asyncio
async def test_database_check_succeeds_against_real_dev_db():
    # Uses the module's real engine (bound to the test run's DATABASE_URL,
    # which points at a genuinely running Postgres in this environment).
    assert await _check_database_reachable() is True


@pytest.mark.asyncio
async def test_database_check_fails_against_unreachable_host():
    # Regression test for the actual bug found: a well-formed but genuinely
    # dead database must be reported as unreachable, not just "valid".
    dead_engine = create_async_engine(
        "postgresql+asyncpg://postgres:postgres@localhost:59999/nonexistent"
    )
    try:
        assert await _check_database_reachable(timeout_seconds=1.0, db_engine=dead_engine) is False
    finally:
        await dead_engine.dispose()


@pytest.mark.asyncio
async def test_redis_check_is_true_when_backend_is_not_redis():
    assert await _check_redis_reachable(cache_backend="memory") is True


@pytest.mark.asyncio
async def test_redis_check_fails_against_unreachable_host():
    result = await _check_redis_reachable(
        timeout_seconds=1.0,
        cache_backend="redis",
        redis_url="redis://localhost:59998/0",
    )
    assert result is False
