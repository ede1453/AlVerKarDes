from app.domains.llm_orchestration.provider_routing_policy import ProviderRoutingPolicy


def test_provider_routing_policy_deduplicates_provider_order():
    order = ProviderRoutingPolicy().build_provider_order(
        preferred_provider="openai",
        fallback_providers=["mock", "openai", "local"],
    )

    assert order == ["openai", "mock", "local"]


def test_provider_routing_policy_status_rules():
    policy = ProviderRoutingPolicy()

    assert policy.is_success("COMPLETED") is True
    assert policy.should_try_next("PROVIDER_NOT_CONFIGURED") is True
    assert policy.should_try_next("BLOCKED") is False
