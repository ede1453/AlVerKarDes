from app.core.runtime_settings import load_runtime_settings


def test_rc601_external_providers_enabled_reads_plural_env_name(monkeypatch):
    monkeypatch.delenv("AICI_EXTERNAL_PROVIDER_ENABLED", raising=False)
    monkeypatch.setenv("AICI_EXTERNAL_PROVIDERS_ENABLED", "true")

    settings = load_runtime_settings()

    assert settings.external_providers_enabled is True


def test_rc601_external_providers_enabled_keeps_singular_env_backward_compatibility(monkeypatch):
    monkeypatch.delenv("AICI_EXTERNAL_PROVIDERS_ENABLED", raising=False)
    monkeypatch.setenv("AICI_EXTERNAL_PROVIDER_ENABLED", "true")

    settings = load_runtime_settings()

    assert settings.external_providers_enabled is True


def test_rc601_plural_env_name_has_priority(monkeypatch):
    monkeypatch.setenv("AICI_EXTERNAL_PROVIDERS_ENABLED", "false")
    monkeypatch.setenv("AICI_EXTERNAL_PROVIDER_ENABLED", "true")

    settings = load_runtime_settings()

    assert settings.external_providers_enabled is False
