from app.domains.llm_provider_gateway.provider_settings import LLMProviderSettings


def test_provider_settings_defaults_to_external_disabled():
    settings = LLMProviderSettings()

    assert settings.enable_external_llm_providers is False
    assert settings.openai_api_key is None
    assert settings.local_provider_enabled is False
