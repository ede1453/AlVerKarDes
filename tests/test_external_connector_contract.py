from decimal import Decimal

import pytest

from app.domains.connectors.external_connector_registry import ExternalConnectorRegistry
from app.domains.connectors.external_contract import ExternalConnectorOffer


def test_external_connector_offer_contract():
    offer = ExternalConnectorOffer(
        source="example",
        title="Apple MacBook Air M5 16GB 512GB",
        url="https://example.com/product",
        price=Decimal("849.00"),
        currency="EUR",
        availability="in_stock",
        brand="Apple",
        confidence=90,
    )

    assert offer.source == "example"
    assert offer.currency == "EUR"
    assert offer.price == Decimal("849.00")


def test_external_connector_registry_sources():
    sources = ExternalConnectorRegistry().list_sources()

    assert "amazon-de" in sources
    assert "mediamarkt-de" in sources
    assert "saturn-de" in sources


@pytest.mark.asyncio
async def test_placeholder_connectors_return_empty_lists(monkeypatch):
    monkeypatch.delenv("EXTERNAL_CONNECTOR_FIXTURE_MODE", raising=False)
    monkeypatch.delenv("MEDIAMARKT_FIXTURE_PATH", raising=False)
    
    connectors = ExternalConnectorRegistry().build_default_connectors()

    for connector in connectors:
        result = await connector.search("M5")
        assert result == []
