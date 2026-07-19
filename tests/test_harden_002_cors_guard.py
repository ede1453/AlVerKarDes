import pytest

from app.core.production_hardening import parse_cors_origins, validate_cors
from app.main import InvalidCorsConfigError, enforce_cors_policy

# The literal value that was live in .env.prod before HARDEN-002 -- not https,
# would have been rejected by this guard.
REAL_WORLD_INSECURE_ORIGIN = "http://localhost:3000"


def test_real_world_insecure_origin_fails_production_cors_validation():
    result = validate_cors(parse_cors_origins(REAL_WORLD_INSECURE_ORIGIN), production=True)
    assert result["valid"] is False
    assert "HTTPS_REQUIRED:http://localhost:3000" in result["errors"]


def test_enforce_cors_policy_blocks_http_origin_in_production():
    with pytest.raises(InvalidCorsConfigError):
        enforce_cors_policy(app_env="production", cors_origins=["http://localhost:3000"])


def test_enforce_cors_policy_blocks_missing_origins_in_production():
    with pytest.raises(InvalidCorsConfigError):
        enforce_cors_policy(app_env="production", cors_origins=[])


def test_enforce_cors_policy_blocks_wildcard_in_production():
    with pytest.raises(InvalidCorsConfigError):
        enforce_cors_policy(app_env="production", cors_origins=["*"])


def test_enforce_cors_policy_blocks_malformed_origin_in_production():
    with pytest.raises(InvalidCorsConfigError):
        enforce_cors_policy(app_env="production", cors_origins=["not-a-url"])


def test_enforce_cors_policy_allows_valid_https_origin_in_production():
    enforce_cors_policy(app_env="production", cors_origins=["https://app.example.com"])  # must not raise


def test_enforce_cors_policy_is_inactive_outside_production():
    enforce_cors_policy(app_env="local", cors_origins=[])
    enforce_cors_policy(app_env="test", cors_origins=["*"])
