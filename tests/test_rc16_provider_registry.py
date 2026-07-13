from app.domains.llm_provider_gateway.provider_registry import LLMProviderRegistry


def test_provider_registry_lists_mock_openai_and_local():
    registry = LLMProviderRegistry()

    names = registry.list_provider_names()

    assert names == ["local", "mock", "openai"]


def test_provider_registry_describes_providers():
    description = LLMProviderRegistry().describe()

    names = {item["name"] for item in description}

    assert {"mock", "openai", "local"}.issubset(names)
    assert any(item["name"] == "mock" and item["default"] is True for item in description)
