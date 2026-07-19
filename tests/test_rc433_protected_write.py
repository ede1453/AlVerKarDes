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


def test_rc433_protected_write():
    assert route_auth_coverage([{'path':'/api/v1/x','methods':['POST'],'protected':True}])['unprotected_write_count']==0
