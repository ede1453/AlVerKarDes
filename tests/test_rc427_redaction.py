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


def test_rc427_redaction():
    assert redacted_environment({'JWT_SECRET':'abc','APP_ENV':'test'})['JWT_SECRET']=='<REDACTED>'
