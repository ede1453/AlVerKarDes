from app.domains.llm_provider_gateway.provider_registry import LLMProviderRegistry


def test_provider_registry_keeps_existing_provider_names():
    registry = LLMProviderRegistry()

    assert registry.list_provider_names() == ["local", "mock", "openai"]


def test_provider_registry_describe_is_backward_compatible_and_plugin_aware():
    description = LLMProviderRegistry().describe()

    names = {item["name"] for item in description}

    assert {"mock", "openai", "local"}.issubset(names)
    assert any(item["name"] == "mock" and item["default"] is True for item in description)
    assert all("plugin_registered" in item for item in description)
