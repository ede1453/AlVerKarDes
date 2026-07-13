from app.domains.llm_provider_gateway.provider_discovery import LLMProviderDiscovery
from app.domains.llm_provider_gateway.provider_plugin import LLMProviderPlugin
from app.domains.llm_provider_gateway.provider_settings import LLMProviderSettings


class LLMProviderRegistry:
    def __init__(
        self,
        settings: LLMProviderSettings | None = None,
        extra_plugins: list[LLMProviderPlugin] | None = None,
    ):
        self.settings = settings or LLMProviderSettings.from_environment()
        self._plugin_registry = LLMProviderDiscovery(self.settings).discover(
            extra_plugins=extra_plugins
        )
        self._providers = {
            name: self._plugin_registry.create_provider(name)
            for name in self._plugin_registry.list_names()
        }

    def get(self, provider_name: str):
        return self._providers.get(provider_name)

    def list_provider_names(self) -> list[str]:
        return sorted(self._providers.keys())

    def describe(self) -> list[dict]:
        descriptions = []

        for plugin in self._plugin_registry.list_plugins():
            descriptions.append(
                {
                    "name": plugin.name,
                    "available": self._providers.get(plugin.name) is not None,
                    "default": plugin.default,
                    "external": plugin.external,
                    "description": plugin.description,
                    "plugin_registered": True,
                }
            )

        return descriptions
