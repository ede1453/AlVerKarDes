import pytest

from app.domains.connectors.manager import ConnectorManager
from app.domains.connectors.manual_connector import ManualConnector
from app.domains.connectors.sdk import ConnectorProductResult


@pytest.mark.asyncio
async def test_connector_manager_searches_all_connectors():
    manager = ConnectorManager([
        ManualConnector([
            ConnectorProductResult(
                source="amazon",
                title="Apple MacBook Air M5 16GB 512GB",
                url="https://amazon.example/a",
                price=849,
                currency="EUR",
                availability="in_stock",
                confidence=95,
            )
        ]),
        ManualConnector([
            ConnectorProductResult(
                source="mediamarkt",
                title="Apple MBA M5 16 GB 512 GB",
                url="https://mm.example/a",
                price=879,
                currency="EUR",
                availability="in_stock",
                confidence=90,
            )
        ]),
    ])

    result = await manager.search_all("Apple")

    assert len(result.offers) == 2
    assert result.errors == []
    assert result.offers[0].price == 849
    assert result.offers[0].canonical_confidence >= 90


@pytest.mark.asyncio
async def test_connector_manager_dedupes_same_url():
    manager = ConnectorManager([
        ManualConnector([
            ConnectorProductResult(
                source="amazon",
                title="Apple MacBook Air M5 16GB 512GB",
                url="https://amazon.example/a",
                price=899,
                confidence=80,
            ),
            ConnectorProductResult(
                source="amazon",
                title="Apple MacBook Air M5 16GB 512GB",
                url="https://amazon.example/a",
                price=849,
                confidence=95,
            ),
        ])
    ])

    result = await manager.search_all("Apple")

    assert len(result.offers) == 1
    assert result.offers[0].price == 849
    assert result.offers[0].overall_confidence > 80


@pytest.mark.asyncio
async def test_connector_manager_handles_connector_error():
    class BrokenConnector:
        source_name = "broken"

        async def search(self, query: str, country: str = "DE"):
            raise RuntimeError("connector failed")

        async def get_product(self, url: str):
            raise RuntimeError("connector failed")

    manager = ConnectorManager([
        ManualConnector([
            ConnectorProductResult(
                source="amazon",
                title="Apple MacBook Air M5 16GB 512GB",
                price=849,
                confidence=95,
            )
        ]),
        BrokenConnector(),
    ])

    result = await manager.search_all("Apple")

    assert len(result.offers) == 1
    assert len(result.errors) == 1
    assert result.errors[0]["connector"] == "broken"
