import pytest

from app.main import WeakDatabasePasswordError, enforce_db_password_strength

# The literal value found deployed in the running "production" container's
# docker-compose.prod.yml POSTGRES_PASSWORD during the LAUNCH-000 investigation
# (2026-07-23).
REAL_WORLD_WEAK_PASSWORD_URL = "postgresql+asyncpg://postgres:12345678@aici-db/aici"


def test_enforce_db_password_strength_blocks_the_real_deployed_password():
    with pytest.raises(WeakDatabasePasswordError):
        enforce_db_password_strength(app_env="production", database_url=REAL_WORLD_WEAK_PASSWORD_URL)


def test_enforce_db_password_strength_blocks_short_password_in_production():
    with pytest.raises(WeakDatabasePasswordError):
        enforce_db_password_strength(
            app_env="production",
            database_url="postgresql+asyncpg://postgres:too-short@db/aici",
        )


def test_enforce_db_password_strength_blocks_missing_password_in_production():
    with pytest.raises(WeakDatabasePasswordError):
        enforce_db_password_strength(app_env="production", database_url="postgresql+asyncpg://postgres@db/aici")


def test_enforce_db_password_strength_allows_strong_password_in_production():
    strong_url = "postgresql+asyncpg://postgres:Aa1!Aa1!Aa1!Aa1!Aa1!Aa1!Aa1!Aa1!@db/aici"
    enforce_db_password_strength(app_env="production", database_url=strong_url)  # must not raise


def test_enforce_db_password_strength_is_inactive_outside_production():
    # The guard is intentionally narrow: it only fails fast in production.
    # Local/dev/test environments keep working with any placeholder password.
    enforce_db_password_strength(app_env="local", database_url=REAL_WORLD_WEAK_PASSWORD_URL)
    enforce_db_password_strength(app_env="test", database_url="postgresql+asyncpg://postgres:too-short@db/aici")
