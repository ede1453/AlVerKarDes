from app.core.runtime_settings import (
    RuntimeSettings,
    runtime_settings_status,
    validate_runtime_settings,
)


def test_rc60_runtime_settings_default_local_is_valid():
    status = runtime_settings_status(RuntimeSettings())

    assert status["status"] == "VALID"
    assert status["issue_count"] == 0


def test_rc60_runtime_settings_detects_invalid_environment():
    issues = validate_runtime_settings(RuntimeSettings(environment="prod"))

    assert any(issue["code"] == "INVALID_ENVIRONMENT" for issue in issues)


def test_rc60_runtime_settings_blocks_debug_in_production():
    issues = validate_runtime_settings(RuntimeSettings(environment="production", debug=True, default_llm_provider="openai", external_providers_enabled=True))

    assert any(issue["code"] == "DEBUG_ENABLED_IN_PRODUCTION" for issue in issues)


def test_rc60_runtime_settings_blocks_external_provider_when_disabled():
    issues = validate_runtime_settings(RuntimeSettings(default_llm_provider="openai", external_providers_enabled=False))

    assert any(issue["code"] == "EXTERNAL_PROVIDER_SELECTED_BUT_DISABLED" for issue in issues)
