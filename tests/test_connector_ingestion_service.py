import pytest

from app.domains.connectors.ingestion_service import ConnectorIngestionService
from app.domains.connectors.manager import ConnectorManager
from app.domains.connectors.manual_connector import ManualConnector
from app.domains.connectors.sdk import ConnectorProductResult


class DummyDB:
    async def rollback(self):
        return None


class DummyProduct:
    def __init__(self, id):
        self.id = id


class DummyStore:
    def __init__(self, id):
        self.id = id


class DummyOffer:
    def __init__(self, id):
        self.id = id


class DummyPrice:
    def __init__(self, id):
        self.id = id


class FakeProductService:
    async def get_or_create_product(self, product_name: str, country: str = "DE"):
        return DummyProduct("11111111-1111-1111-1111-111111111111"), {"identity": "ok"}, True


class FakeMarketService:
    async def create_store(self, payload):
        return DummyStore("22222222-2222-2222-2222-222222222222")

    async def get_or_create_offer(self, payload):
        return DummyOffer("33333333-3333-3333-3333-333333333333"), True

    async def save_price_snapshot(self, payload):
        return DummyPrice("44444444-4444-4444-4444-444444444444")


@pytest.mark.asyncio
async def test_connector_ingestion_ingests_offers(monkeypatch):
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
        ])
    ])

    service = ConnectorIngestionService(db=DummyDB(), manager=manager)
    service.product_service = FakeProductService()
    service.market_service = FakeMarketService()

    result = await service.search_and_ingest("Apple")

    assert result.total_offers == 1
    assert result.ingested_count == 1
    assert result.items[0].status == "INGESTED"
    assert result.items[0].product_id == "11111111-1111-1111-1111-111111111111"


@pytest.mark.asyncio
async def test_connector_ingestion_skips_missing_price():
    manager = ConnectorManager([
        ManualConnector([
            ConnectorProductResult(
                source="amazon",
                title="Apple MacBook Air M5 16GB 512GB",
                url="https://amazon.example/a",
                price=None,
                confidence=95,
            )
        ])
    ])

    service = ConnectorIngestionService(db=DummyDB(), manager=manager)
    service.product_service = FakeProductService()
    service.market_service = FakeMarketService()

    result = await service.search_and_ingest("Apple")

    assert result.total_offers == 1
    assert result.ingested_count == 0
    assert result.items[0].status == "SKIPPED"
    assert result.items[0].error == "missing_price"
