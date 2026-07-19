import pytest

from app.core.production_hardening import validate_request_body_limit
from app.main import InvalidRequestBodyLimitError, enforce_request_body_limit_policy


def test_default_2mib_limit_is_valid_in_production():
    result = validate_request_body_limit(2_097_152, production=True)
    assert result["valid"] is True


def test_zero_limit_is_invalid():
    result = validate_request_body_limit(0, production=True)
    assert result["valid"] is False
    assert "REQUEST_BODY_LIMIT_MUST_BE_POSITIVE" in result["errors"]


def test_negative_limit_is_invalid():
    result = validate_request_body_limit(-1, production=True)
    assert result["valid"] is False
    assert "REQUEST_BODY_LIMIT_MUST_BE_POSITIVE" in result["errors"]


def test_absurdly_large_limit_is_invalid_in_production():
    result = validate_request_body_limit(500 * 1024 * 1024, production=True)
    assert result["valid"] is False
    assert "REQUEST_BODY_LIMIT_TOO_LARGE_FOR_PRODUCTION" in result["errors"]


def test_enforce_request_body_limit_policy_blocks_zero_in_production():
    with pytest.raises(InvalidRequestBodyLimitError):
        enforce_request_body_limit_policy(app_env="production", maximum_bytes=0)


def test_enforce_request_body_limit_policy_allows_default_in_production():
    enforce_request_body_limit_policy(app_env="production", maximum_bytes=2_097_152)  # must not raise


def test_enforce_request_body_limit_policy_is_inactive_outside_production():
    enforce_request_body_limit_policy(app_env="local", maximum_bytes=0)
    enforce_request_body_limit_policy(app_env="test", maximum_bytes=-1)
