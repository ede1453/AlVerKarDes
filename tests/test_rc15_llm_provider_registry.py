from app.domains.llm_provider_gateway.provider_registry import LLMProviderRegistry


def test_llm_provider_registry_contains_mock_provider():
    registry = LLMProviderRegistry()

    assert registry.get("mock") is not None
    assert "mock" in registry.list_provider_names()
