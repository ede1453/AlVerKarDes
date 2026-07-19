import pytest

from app.core.production_hardening import security_headers
from app.main import MissingSecurityHeadersError, enforce_security_headers_policy


def test_security_headers_now_include_csp():
    # HARDEN-004: Content-Security-Policy was entirely absent before this
    # change, even though it's one of the headers this domain's own
    # description ("HSTS, X-Frame-Options, CSP") called out as expected.
    headers = security_headers(production=True)
    assert headers["Content-Security-Policy"] == "default-src 'none'; frame-ancestors 'none'"


def test_enforce_security_headers_policy_allows_complete_headers_in_production():
    enforce_security_headers_policy(
        app_env="production", headers=security_headers(production=True)
    )  # must not raise


def test_enforce_security_headers_policy_blocks_missing_hsts_in_production():
    # Simulates the real regression this guard protects against: HSTS silently
    # dropped from security_headers()'s output (e.g. someone deletes the `if
    # production:` block by accident).
    broken_headers = security_headers(production=True)
    del broken_headers["Strict-Transport-Security"]

    with pytest.raises(MissingSecurityHeadersError):
        enforce_security_headers_policy(app_env="production", headers=broken_headers)


def test_enforce_security_headers_policy_blocks_missing_csp_in_production():
    broken_headers = security_headers(production=True)
    del broken_headers["Content-Security-Policy"]

    with pytest.raises(MissingSecurityHeadersError):
        enforce_security_headers_policy(app_env="production", headers=broken_headers)


def test_enforce_security_headers_policy_is_inactive_outside_production():
    enforce_security_headers_policy(app_env="local", headers={})
    enforce_security_headers_policy(app_env="test", headers={})
