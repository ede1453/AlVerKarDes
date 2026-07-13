from app.core.runtime_settings import load_runtime_settings


def test_rc60_runtime_settings_loads_environment_variables(monkeypatch):
    monkeypatch.setenv("AICI_ENVIRONMENT", "staging")
    monkeypatch.setenv("AICI_DEFAULT_LLM_PROVIDER", "openai")
    monkeypatch.setenv("AICI_EXTERNAL_PROVIDERS_ENABLED", "true")
    monkeypatch.setenv("AICI_CACHE_BACKEND", "redis")
    monkeypatch.setenv("AICI_NOTIFICATION_PROVIDER", "external")
    monkeypatch.setenv("AICI_DEBUG", "false")

    settings = load_runtime_settings()

    assert settings.environment == "staging"
    assert settings.default_llm_provider == "openai"
    assert settings.external_providers_enabled is True
    assert settings.cache_backend == "redis"
    assert settings.notification_provider == "external"
    assert settings.debug is False
