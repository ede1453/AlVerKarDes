from app.domains.llm_provider_gateway.mock_provider import MockLLMProvider
from app.domains.llm_provider_gateway.provider_plugin import (
    LLMProviderPlugin,
    LLMProviderPluginRegistry,
)
from app.domains.llm_provider_gateway.provider_settings import LLMProviderSettings
from app.domains.llm_provider_gateway.providers.local_provider import LocalLLMProvider
from app.domains.llm_provider_gateway.providers.openai_provider import OpenAICompatibleProvider


def build_default_provider_plugin_registry(
    settings: LLMProviderSettings | None = None,
) -> LLMProviderPluginRegistry:
    settings = settings or LLMProviderSettings.from_environment()
    registry = LLMProviderPluginRegistry()

    registry.register(
        LLMProviderPlugin(
            name="mock",
            default=True,
            external=False,
            description="Offline deterministic mock provider.",
            factory=lambda: MockLLMProvider(),
        )
    )

    registry.register(
        LLMProviderPlugin(
            name="openai",
            default=False,
            external=True,
            description="OpenAI-compatible provider boundary.",
            factory=lambda: OpenAICompatibleProvider(
                api_key=settings.openai_api_key,
                enabled=settings.enable_external_llm_providers,
            ),
        )
    )

    registry.register(
        LLMProviderPlugin(
            name="local",
            default=False,
            external=True,
            description="Local LLM provider boundary.",
            factory=lambda: LocalLLMProvider(
                api_key="local-provider",
                enabled=settings.local_provider_enabled,
            ),
        )
    )

    return registry
