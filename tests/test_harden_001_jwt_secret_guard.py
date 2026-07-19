import pytest

from app.core.production_hardening import is_placeholder, secret_strength
from app.main import WeakJwtSecretError, enforce_jwt_secret_strength

# The literal value found deployed in the running "production" container's
# JWT_SECRET env var during the HARDEN-001 investigation (2026-07-18).
REAL_WORLD_WEAK_SECRET = "EN_AZ_32_KARAKTERLIK_GUCLU_RASTGELE_SECRET"


def test_real_world_weak_secret_is_flagged_as_placeholder():
    # Regression test: before HARDEN-001, PLACEHOLDER_MARKERS only covered
    # English conventions and secret_strength() alone (length + character
    # classes) accepted this value, so the guard would NOT have caught it.
    assert is_placeholder(REAL_WORLD_WEAK_SECRET) is True
    assert secret_strength(REAL_WORLD_WEAK_SECRET)["valid"] is False


def test_enforce_jwt_secret_strength_blocks_the_real_deployed_secret():
    with pytest.raises(WeakJwtSecretError):
        enforce_jwt_secret_strength(app_env="production", jwt_secret=REAL_WORLD_WEAK_SECRET)


def test_enforce_jwt_secret_strength_blocks_short_secret_in_production():
    with pytest.raises(WeakJwtSecretError):
        enforce_jwt_secret_strength(app_env="production", jwt_secret="too-short")


def test_enforce_jwt_secret_strength_blocks_missing_secret_in_production():
    with pytest.raises(WeakJwtSecretError):
        enforce_jwt_secret_strength(app_env="production", jwt_secret=None)


def test_enforce_jwt_secret_strength_allows_strong_secret_in_production():
    strong = "Aa1!" * 12
    enforce_jwt_secret_strength(app_env="production", jwt_secret=strong)  # must not raise


def test_enforce_jwt_secret_strength_is_inactive_outside_production():
    # The guard is intentionally narrow: it only fails fast in production.
    # Local/dev/test environments keep working with any placeholder secret.
    enforce_jwt_secret_strength(app_env="local", jwt_secret=REAL_WORLD_WEAK_SECRET)
    enforce_jwt_secret_strength(app_env="test", jwt_secret="too-short")
