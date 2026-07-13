from app.domains.llm_provider_gateway.mock_provider import MockLLMProvider
from app.domains.llm_provider_gateway.provider_discovery import LLMProviderDiscovery
from app.domains.llm_provider_gateway.provider_plugin import LLMProviderPlugin


def test_provider_discovery_loads_default_plugins():
    registry = LLMProviderDiscovery().discover()

    assert registry.list_names() == ["local", "mock", "openai"]


def test_provider_discovery_accepts_extra_plugins():
    registry = LLMProviderDiscovery().discover(
        extra_plugins=[
            LLMProviderPlugin(
                name="custom",
                factory=lambda: MockLLMProvider(),
                description="Custom test provider.",
            )
        ]
    )

    assert "custom" in registry.list_names()
