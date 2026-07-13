from app.domains.marketplace_connectors.connector_registry import MarketplaceConnectorRegistry


def test_marketplace_connector_registry_contains_mock_and_external_boundaries():
    registry = MarketplaceConnectorRegistry()

    names = [connector["name"] for connector in registry.list()]

    assert "mock_marketplace" in names
    assert "amazon" in names
    assert "idealo" in names


def test_marketplace_connector_registry_returns_connector():
    registry = MarketplaceConnectorRegistry()

    assert registry.get("mock_marketplace") is not None
    assert registry.get("missing") is None
