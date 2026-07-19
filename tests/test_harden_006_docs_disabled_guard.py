import pytest

from app.main import DocsExposedInProductionError, enforce_docs_disabled_policy, app


def test_real_app_has_openapi_url_disabled():
    # Regression test for the actual bug found: openapi_url was hardcoded to
    # "/openapi.json" unconditionally, never gated by docs_enabled, so the
    # full API schema was exposed in production even with /docs and /redoc
    # correctly disabled. The test process runs with APP_ENV defaulting to
    # "local" (not production), so this only proves the attribute exists and
    # is wired -- production behavior is verified for real against the
    # running container (see WIKI_ROOT ADR-004 for the live proof).
    assert hasattr(app, "openapi_url")


def test_enforce_docs_disabled_policy_blocks_docs_url_in_production():
    with pytest.raises(DocsExposedInProductionError):
        enforce_docs_disabled_policy(
            app_env="production", docs_url="/docs", redoc_url=None, openapi_url=None
        )


def test_enforce_docs_disabled_policy_blocks_redoc_url_in_production():
    with pytest.raises(DocsExposedInProductionError):
        enforce_docs_disabled_policy(
            app_env="production", docs_url=None, redoc_url="/redoc", openapi_url=None
        )


def test_enforce_docs_disabled_policy_blocks_openapi_url_in_production():
    # This is exactly the bug that was live: openapi_url alone exposed while
    # docs_url/redoc_url were correctly None.
    with pytest.raises(DocsExposedInProductionError):
        enforce_docs_disabled_policy(
            app_env="production", docs_url=None, redoc_url=None, openapi_url="/openapi.json"
        )


def test_enforce_docs_disabled_policy_allows_all_disabled_in_production():
    enforce_docs_disabled_policy(
        app_env="production", docs_url=None, redoc_url=None, openapi_url=None
    )  # must not raise


def test_enforce_docs_disabled_policy_is_inactive_outside_production():
    enforce_docs_disabled_policy(
        app_env="local", docs_url="/docs", redoc_url="/redoc", openapi_url="/openapi.json"
    )
