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


def test_rc434_environment_ready():
    assert evaluate_environment({'APP_ENV':'production','DEBUG':'false','DATABASE_URL':'postgresql+asyncpg://u:p@db:5432/a','REDIS_URL':'redis://redis:6379/0','JWT_SECRET':'Aa1!'*12,'CORS_ALLOWED_ORIGINS':'https://app.test','TRUSTED_HOSTS':'api.test'})['ready'] is True
