from decimal import Decimal

import pytest

from app.domains.connectors.external_contract import ExternalConnectorOffer
from app.domains.connectors.external_ingestion_service import ExternalConnectorIngestionService
from app.domains.connectors.ingestion_service import ConnectorIngestionResult, IngestedOfferResult


class DummyDB:
    pass


class FakeBridge:
    async def search_all(self, query: str, country: str = "DE"):
        return {
            "query": query,
            "country": country,
            "results": [
                ExternalConnectorOffer(
                    source="mediamarkt-de",
                    title="Apple MacBook Air M5 16 GB 512 GB",
                    url="https://example.com/mm",
                    price=Decimal("879.00"),
                    currency="EUR",
                    availability="in_stock",
                    brand="Apple",
                    confidence=87,
                )
            ],
            "errors": [],
        }


class FakeIngestionService:
    def __init__(self, db, manager):
        self.db = db
        self.manager = manager

    async def search_and_ingest(self, query: str, country: str = "DE"):
        return ConnectorIngestionResult(
            query=query,
            country=country,
            total_offers=1,
            ingested_count=1,
            skipped_count=0,
            items=[
                IngestedOfferResult(
                    source="mediamarkt-de",
                    title="Apple MacBook Air M5 16 GB 512 GB",
                    canonical_key="apple::macbook-air::m5::16gb::512gb::de",
                    product_id="11111111-1111-1111-1111-111111111111",
                    store_id="22222222-2222-2222-2222-222222222222",
                    offer_id="33333333-3333-3333-3333-333333333333",
                    price_id="44444444-4444-4444-4444-444444444444",
                    status="INGESTED",
                )
            ],
            connector_errors=[],
        )


@pytest.mark.asyncio
async def test_external_connector_ingestion_service(monkeypatch):
    import app.domains.connectors.external_ingestion_service as module

    monkeypatch.setattr(module, "ExternalConnectorBridge", lambda connectors: FakeBridge())
    monkeypatch.setattr(module, "ConnectorIngestionService", FakeIngestionService)

    result = await ExternalConnectorIngestionService(DummyDB()).search_and_ingest("M5")

    assert result["external_offer_count"] == 1
    assert result["ingestion"]["ingested_count"] == 1
    assert result["ingestion"]["items"][0]["source"] == "mediamarkt-de"
