import pytest

from app.domains.llm_provider_gateway.mock_provider import MockLLMProvider
from app.domains.llm_provider_gateway.provider_plugin import (
    LLMProviderPlugin,
    LLMProviderPluginRegistry,
)


def test_provider_plugin_registry_registers_and_creates_provider():
    registry = LLMProviderPluginRegistry()

    registry.register(
        LLMProviderPlugin(
            name="test-mock",
            factory=lambda: MockLLMProvider(),
        )
    )

    provider = registry.create_provider("test-mock")

    assert provider is not None
    assert provider.name == "mock"


def test_provider_plugin_registry_rejects_duplicate_plugin_names():
    registry = LLMProviderPluginRegistry()
    plugin = LLMProviderPlugin(name="mock", factory=lambda: MockLLMProvider())

    registry.register(plugin)

    with pytest.raises(ValueError):
        registry.register(plugin)
