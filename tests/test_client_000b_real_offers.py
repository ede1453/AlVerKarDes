"""CLIENT-000b (ADR-010): shopping_pipeline's search/offer step must read
REAL ingested offers from market.Offer/Price, not fabricate a listing.
Previously _default_offers() (removed) always returned a hardcoded
"Apple {query}" @ Saturn 949.00 / Amazon 999.00 pair whenever the caller
didn't supply `offers` explicitly -- the exact same fabrication pattern
CONNECT-001 removed from price_history, but never removed from here (see
WIKI_ROOT 07-Issues-Risks/Shopping-Pipeline-Sahte-Arama-Verisi-CLIENT-000).
"""

import uuid

import pytest

from app.core.database import AsyncSessionLocal
from app.domains.market.schemas import OfferCreate, PriceSnapshotCreate, StoreCreate
from app.domains.market.service import MarketService
from app.domains.products.service import ProductService
from app.domains.shopping_pipeline.pipeline_service import ShoppingPipelineService


@pytest.mark.asyncio
async def test_real_offers_returns_actual_ingested_offer_not_fabricated():
    product_name = f"CLIENT-000b Test Monitor {uuid.uuid4().hex[:8]}"

    async with AsyncSessionLocal() as db:
        product, _identity, _created = await ProductService(db).create_from_name(product_name, country="DE")
        market = MarketService(db)
        store = await market.create_store(
            StoreCreate(name="CLIENT-000b Test Store", slug=f"client-000b-{uuid.uuid4().hex[:8]}", country="DE")
        )
        offer, _ = await market.get_or_create_offer(
            OfferCreate(product_id=product.id, store_id=store.id, url=f"https://example.com/client-000b-{uuid.uuid4().hex[:8]}")
        )
        await market.save_price_snapshot(
            PriceSnapshotCreate(offer_id=offer.id, amount=199.00, currency="EUR", is_real_data=True)
        )

    service = ShoppingPipelineService()
    async with AsyncSessionLocal() as db:
        offers = await service._real_offers(db, product_name)

    assert offers, "expected a real offer to be returned"
    assert offers[0]["marketplace"] == "CLIENT-000b Test Store"
    assert offers[0]["price"] == "199.00"
    # The old bug's tell: nothing here should be the fabricated fallback.
    assert not any(o["price"] in ("949.00", "999.00") for o in offers)
    assert not any(o["marketplace"] in ("saturn", "amazon") and o["product_name"].startswith("Apple ") for o in offers)


@pytest.mark.asyncio
async def test_real_offers_returns_empty_list_when_nothing_ingested():
    never_ingested_query = f"Totally Unseen Product {uuid.uuid4().hex[:8]}"

    service = ShoppingPipelineService()
    async with AsyncSessionLocal() as db:
        offers = await service._real_offers(db, never_ingested_query)

    assert offers == []


@pytest.mark.asyncio
async def test_run_with_never_ingested_query_returns_no_recommendation_not_fabricated_offer():
    service = ShoppingPipelineService()
    async with AsyncSessionLocal() as db:
        result = await service.run(
            {"user_id": str(uuid.uuid4()), "query": f"Totally Unseen Query {uuid.uuid4().hex[:8]}"},
            db,
        )

    assert result["status"] == "NO_RECOMMENDATION"
    assert result["top_recommendation"] is None
    assert result["price_history"] is None
    assert "949.00" not in str(result)
    assert "999.00" not in str(result)


@pytest.mark.asyncio
async def test_run_with_real_ingested_product_surfaces_real_offer_and_price_history():
    product_name = f"CLIENT-000b E2E Product {uuid.uuid4().hex[:8]}"

    async with AsyncSessionLocal() as db:
        product, identity, _created = await ProductService(db).create_from_name(product_name, country="DE")
        market = MarketService(db)
        store = await market.create_store(
            StoreCreate(name="CLIENT-000b E2E Store", slug=f"client-000b-e2e-{uuid.uuid4().hex[:8]}", country="DE")
        )
        offer, _ = await market.get_or_create_offer(
            OfferCreate(product_id=product.id, store_id=store.id, url=f"https://example.com/client-000b-e2e-{uuid.uuid4().hex[:8]}")
        )
        await market.save_price_snapshot(
            PriceSnapshotCreate(offer_id=offer.id, amount=249.00, currency="EUR", is_real_data=True)
        )

    service = ShoppingPipelineService()
    async with AsyncSessionLocal() as db:
        result = await service.run({"user_id": str(uuid.uuid4()), "query": product_name}, db)

    assert result["status"] == "COMPLETED"
    assert result["top_recommendation"]["product_key"] == identity.canonical_key
    assert result["price_history"]["status"] == "OK"
    assert result["price_history"]["latest_price"] == "249.00"
