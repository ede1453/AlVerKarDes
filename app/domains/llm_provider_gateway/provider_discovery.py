from app.domains.llm_provider_gateway.default_provider_plugins import (
    build_default_provider_plugin_registry,
)
from app.domains.llm_provider_gateway.provider_plugin import (
    LLMProviderPlugin,
    LLMProviderPluginRegistry,
)
from app.domains.llm_provider_gateway.provider_settings import LLMProviderSettings


class LLMProviderDiscovery:
    def __init__(self, settings: LLMProviderSettings | None = None):
        self.settings = settings or LLMProviderSettings.from_environment()

    def discover(self, extra_plugins: list[LLMProviderPlugin] | None = None) -> LLMProviderPluginRegistry:
        registry = build_default_provider_plugin_registry(self.settings)

        for plugin in extra_plugins or []:
            registry.register(plugin)

        return registry
