from pathlib import Path
from app.core.production_hardening import (
    connector_fixture_violations,
    evaluate_environment,
    is_placeholder,
    parse_cors_origins,
    path_is_release_safe,
    redacted_environment,
    required_connector_credentials,
    route_auth_coverage,
    secret_strength,
    security_headers,
    validate_cors,
    validate_database_url,
    validate_redis_url,
    validate_trusted_hosts,
)


def test_rc420_redis_localhost():
    assert validate_redis_url('redis://localhost:6379/0',production=True)['valid'] is False
