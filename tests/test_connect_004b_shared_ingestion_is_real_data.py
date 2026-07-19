"""PARÇA B (CONNECT-004 devamı, ADR-007): tek paylaşılan ingestion yolu
(ConnectorManager -> ConnectorIngestionService -> market.Price) artık her
üç connector'ı (Amazon/eBay/Idealo) da kapsıyor, connector'a özel ayrı bir
yazma yolu yok. Her yazılan Price satırı is_real_data taşıyor, ve gerçek
tüketici fiyat-geçmişi sinyali (ShoppingPipelineService._real_price_history)
varsayılan olarak sadece is_real_data=true satırları görüyor -- fixture/test
verisi hiçbir zaman gerçek sinyale karışmıyor (CONNECT-001/004'teki sızıntı
korumasıyla aynı disiplin, artık yazma+okuma noktasında da).
"""

import uuid

import pytest

from app.core.database import AsyncSessionLocal
from app.domains.connectors.ingestion_service import ConnectorIngestionService
from app.domains.connectors.manager import ConnectorManager
from app.domains.connectors.manual_connector import ManualConnector
from app.domains.connectors.marketplace_adapters import (
    AmazonStoreConnectorAdapter,
    EbayStoreConnectorAdapter,
    IdealoStoreConnectorAdapter,
)
from app.domains.connectors.sdk import ConnectorProductResult
from app.domains.market.schemas import OfferCreate, PriceSnapshotCreate, StoreCreate
from app.domains.market.service import MarketService
from app.domains.shopping_pipeline.pipeline_service import ShoppingPipelineService


@pytest.mark.asyncio
async def test_amazon_ebay_idealo_adapters_tag_fixture_mode_results_not_real():
    for adapter in (
        AmazonStoreConnectorAdapter(),
        EbayStoreConnectorAdapter(),
        IdealoStoreConnectorAdapter(),
    ):
        results = await adapter.search(query="Example Laptop", country="DE")
        assert results, f"{adapter.source_name} adapter returned no results in fixture mode"
        assert all(item.is_real_data is False for item in results), (
            f"{adapter.source_name} adapter did not tag fixture-mode results as is_real_data=False"
        )


@pytest.mark.asyncio
async def test_all_three_connectors_write_through_the_same_ingestion_service():
    query = f"Unique Test Widget {uuid.uuid4().hex[:8]}"
    manager = ConnectorManager([
        AmazonStoreConnectorAdapter(),
        EbayStoreConnectorAdapter(),
        IdealoStoreConnectorAdapter(),
        ManualConnector([
            ConnectorProductResult(
                source="manual-test",
                title=query,
                url=f"https://example.com/{uuid.uuid4().hex[:8]}",
                price=123.45,
                currency="EUR",
                confidence=90,
                is_real_data=True,
            )
        ]),
    ])

    async with AsyncSessionLocal() as db:
        result = await ConnectorIngestionService(db=db, manager=manager).search_and_ingest(query=query, country="DE")

    # Amazon/eBay/Idealo's fixture transports always return "Example Laptop"
    # regardless of query (consistent, honest fixture behavior across all
    # three) plus the ManualConnector's one unique-titled item -- proves
    # all four sources went through the SAME ConnectorIngestionService,
    # no connector-specific write path or filtering branch.
    sources = {item.source for item in result.items}
    # CONNECT-006: EbayStoreConnectorAdapter()'in varsayılan source_name'i
    # artık "ebay" değil "ebay_de" (çok-ülke desteği, marketplace_id
    # source_name'e yansıyor).
    assert sources == {"amazon", "ebay_de", "idealo", "manual-test"}
    assert result.ingested_count == 4

    is_real_by_source = {item.source: item.is_real_data for item in result.items}
    assert is_real_by_source == {
        "amazon": False,
        "ebay_de": False,
        "idealo": False,
        "manual-test": True,
    }


@pytest.mark.asyncio
async def test_fixture_only_price_history_does_not_leak_into_real_consumer_signal():
    query = f"Fixture Leak Test Product {uuid.uuid4().hex[:8]}"
    manager = ConnectorManager([
        ManualConnector([
            ConnectorProductResult(
                source="fixture-source",
                title=query,
                url=f"https://example.com/{uuid.uuid4().hex[:8]}",
                price=699.99,
                currency="EUR",
                confidence=90,
                is_real_data=False,
            )
        ])
    ])

    async with AsyncSessionLocal() as db:
        result = await ConnectorIngestionService(db=db, manager=manager).search_and_ingest(query=query, country="DE")
        assert result.ingested_count == 1
        canonical_key = result.items[0].canonical_key

    service = ShoppingPipelineService()
    async with AsyncSessionLocal() as db:
        price_history = await service._real_price_history(db, canonical_key)

    assert price_history == {"status": "INSUFFICIENT_DATA", "reason": "NO_PRICE_HISTORY"}
    assert "699.99" not in str(price_history)


@pytest.mark.asyncio
async def test_real_data_price_history_is_visible_to_real_consumer_signal():
    query = f"Real Data Test Product {uuid.uuid4().hex[:8]}"
    manager = ConnectorManager([
        ManualConnector([
            ConnectorProductResult(
                source="real-source",
                title=query,
                url=f"https://example.com/{uuid.uuid4().hex[:8]}",
                price=555.00,
                currency="EUR",
                confidence=90,
                is_real_data=True,
            )
        ])
    ])

    async with AsyncSessionLocal() as db:
        result = await ConnectorIngestionService(db=db, manager=manager).search_and_ingest(query=query, country="DE")
        assert result.ingested_count == 1
        canonical_key = result.items[0].canonical_key

    service = ShoppingPipelineService()
    async with AsyncSessionLocal() as db:
        price_history = await service._real_price_history(db, canonical_key)

    assert price_history["status"] == "OK"
    assert price_history["latest_price"] == "555.00"


@pytest.mark.asyncio
async def test_price_repository_only_real_filter_excludes_fixture_rows_by_default():
    async with AsyncSessionLocal() as db:
        market = MarketService(db)
        store = await market.create_store(
            StoreCreate(name="PARÇA B Test Store", slug=f"parca-b-test-{uuid.uuid4().hex[:8]}", country="DE")
        )

        from app.domains.products.service import ProductService

        product, _identity, _created = await ProductService(db).create_from_name(
            f"Parça B Filter Test Product {uuid.uuid4().hex[:8]}", country="DE"
        )

        offer, _ = await market.get_or_create_offer(
            OfferCreate(
                product_id=product.id,
                store_id=store.id,
                url=f"https://example.com/parca-b-{uuid.uuid4().hex[:8]}",
            )
        )
        await market.save_price_snapshot(
            PriceSnapshotCreate(offer_id=offer.id, amount=100.00, currency="EUR", is_real_data=False)
        )

        default_history = await market.get_price_history_for_product(product.id)
        assert default_history == []

        full_history = await market.get_price_history_for_product(product.id, only_real=False)
        assert len(full_history) == 1
        assert float(full_history[0].amount) == 100.00
