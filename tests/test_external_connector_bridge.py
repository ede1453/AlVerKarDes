from decimal import Decimal

import pytest

from app.domains.connectors.external_connector_bridge import ExternalConnectorBridge
from app.domains.connectors.external_contract import ExternalConnectorOffer
from app.domains.connectors.external_offer_mapper import ExternalOfferMapper


class FakeExternalConnector:
    source = "fake-external"

    async def search(self, query: str, country: str = "DE"):
        return [
            ExternalConnectorOffer(
                source=self.source,
                title="Apple MacBook Air M5 16GB 512GB",
                url="https://example.com/macbook",
                price=Decimal("849.00"),
                currency="EUR",
                availability="in_stock",
                brand="Apple",
                confidence=91,
            )
        ]


class BrokenExternalConnector:
    source = "broken-external"

    async def search(self, query: str, country: str = "DE"):
        raise RuntimeError("connector failed")


def test_external_offer_mapper_maps_to_connector_product_result():
    offer = ExternalConnectorOffer(
        source="external",
        title="Sony WH-1000XM7 Black",
        url="https://example.com/sony",
        price=Decimal("299.99"),
        currency="EUR",
        availability="in_stock",
        brand="Sony",
        confidence=88,
    )

    result = ExternalOfferMapper().to_connector_product_result(offer)

    assert result.source == "external"
    assert result.title == "Sony WH-1000XM7 Black"
    assert result.price == 299.99
    assert result.currency == "EUR"
    assert result.availability == "in_stock"
    assert result.brand == "Sony"
    assert result.confidence == 88


@pytest.mark.asyncio
async def test_external_connector_bridge_returns_connector_product_results():
    bridge = ExternalConnectorBridge([FakeExternalConnector()])

    result = await bridge.search_all("MacBook")

    assert result["query"] == "MacBook"
    assert result["country"] == "DE"
    assert len(result["results"]) == 1
    assert result["results"][0].source == "fake-external"
    assert result["errors"] == []


@pytest.mark.asyncio
async def test_external_connector_bridge_collects_errors():
    bridge = ExternalConnectorBridge([FakeExternalConnector(), BrokenExternalConnector()])

    result = await bridge.search_all("MacBook")

    assert len(result["results"]) == 1
    assert len(result["errors"]) == 1
    assert result["errors"][0]["source"] == "broken-external"
