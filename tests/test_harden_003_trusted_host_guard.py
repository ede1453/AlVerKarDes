import pytest

from app.core.production_hardening import parse_trusted_hosts, validate_trusted_hosts
from app.main import InvalidTrustedHostsConfigError, enforce_trusted_hosts_policy

# TRUSTED_HOSTS was never set in .env.prod before HARDEN-003 -- identical gap
# to CORS_ALLOWED_ORIGINS before HARDEN-002.
REAL_WORLD_MISSING_VALUE = ""


def test_real_world_missing_trusted_hosts_fails_production_validation():
    result = validate_trusted_hosts(parse_trusted_hosts(REAL_WORLD_MISSING_VALUE), production=True)
    assert result["valid"] is False
    assert "TRUSTED_HOSTS_REQUIRED" in result["errors"]


def test_enforce_trusted_hosts_policy_blocks_missing_hosts_in_production():
    with pytest.raises(InvalidTrustedHostsConfigError):
        enforce_trusted_hosts_policy(app_env="production", trusted_hosts=[])


def test_enforce_trusted_hosts_policy_blocks_wildcard_in_production():
    with pytest.raises(InvalidTrustedHostsConfigError):
        enforce_trusted_hosts_policy(app_env="production", trusted_hosts=["*"])


def test_enforce_trusted_hosts_policy_allows_valid_host_in_production():
    enforce_trusted_hosts_policy(app_env="production", trusted_hosts=["localhost"])  # must not raise


def test_enforce_trusted_hosts_policy_is_inactive_outside_production():
    enforce_trusted_hosts_policy(app_env="local", trusted_hosts=[])
    enforce_trusted_hosts_policy(app_env="test", trusted_hosts=["*"])
