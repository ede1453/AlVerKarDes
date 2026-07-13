from dataclasses import dataclass
from typing import Callable

from app.domains.llm_provider_gateway.provider_interface import LLMProvider


@dataclass(frozen=True)
class LLMProviderPlugin:
    name: str
    factory: Callable[[], LLMProvider]
    external: bool = False
    default: bool = False
    description: str | None = None


class LLMProviderPluginRegistry:
    def __init__(self):
        self._plugins: dict[str, LLMProviderPlugin] = {}

    def register(self, plugin: LLMProviderPlugin):
        if plugin.name in self._plugins:
            raise ValueError(f"Duplicate LLM provider plugin: {plugin.name}")

        self._plugins[plugin.name] = plugin
        return plugin

    def get(self, name: str):
        return self._plugins.get(name)

    def list_names(self) -> list[str]:
        return sorted(self._plugins.keys())

    def list_plugins(self) -> list[LLMProviderPlugin]:
        return [self._plugins[name] for name in self.list_names()]

    def create_provider(self, name: str):
        plugin = self.get(name)
        if plugin is None:
            return None

        return plugin.factory()
