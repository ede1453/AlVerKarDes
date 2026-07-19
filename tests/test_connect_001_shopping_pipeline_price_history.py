"""CONNECT-001 regression test: shopping_pipeline must read REAL price
history from market.Price (the canonical store, ADR-007 Karar 3), and must
return an explicit INSUFFICIENT_DATA status rather than fabricating numbers
when no real history exists. Previously it fabricated a "history" from the
current search's offers, falling back to a hardcoded 949.00 when even that
was empty (see WIKI_ROOT 07-Issues-Risks for the incident record).

CONNECT-003 update: ShoppingPipelineService._real_price_history() now takes
a canonical_key directly (trusted from this pipeline's own canonicalization
step, which is real as of CONNECT-003 -- ADR-007 Karar 2), not a product_name
it had to re-normalize itself (that was CONNECT-001's workaround for the
canonicalization mismatch CONNECT-003 fixed at the source).
"""

import uuid

import pytest

from app.core.database import AsyncSessionLocal
from app.domains.market.schemas import OfferCreate, PriceSnapshotCreate, StoreCreate
from app.domains.market.service import MarketService
from app.domains.products.normalization.schemas import ProductNormalizationInput
from app.domains.products.normalization.service import ProductNormalizationService
from app.domains.products.service import ProductService
from app.domains.shopping_pipeline.pipeline_service import ShoppingPipelineService


@pytest.mark.asyncio
async def test_connect_001_real_price_history_is_read_from_market_price():
    # A distinctive, unlikely-to-collide product identity (brand=Sony,
    # family/model=WH-1000XM5) so this test's DB state doesn't depend on
    # what other tests/sessions may have already created.
    product_name = "Sony WH-1000XM5 Wireless Headphones"

    async with AsyncSessionLocal() as db:
        product, identity, _created = await ProductService(db).create_from_name(product_name, country="DE")
        assert identity.canonical_key, "expected the real normalizer to produce a canonical_key for this input"

    async with AsyncSessionLocal() as db:
        market = MarketService(db)
        store = await market.create_store(
            StoreCreate(name="CONNECT-001 Test Store", slug=f"connect-001-test-{uuid.uuid4().hex[:8]}", country="DE")
        )
        offer, _ = await market.get_or_create_offer(
            OfferCreate(
                product_id=product.id,
                store_id=store.id,
                url=f"https://example.com/connect-001-{uuid.uuid4().hex[:8]}",
            )
        )
        await market.save_price_snapshot(
            PriceSnapshotCreate(offer_id=offer.id, amount=349.00, currency="EUR")
        )
        await market.save_price_snapshot(
            PriceSnapshotCreate(offer_id=offer.id, amount=299.00, currency="EUR")
        )

    service = ShoppingPipelineService()
    async with AsyncSessionLocal() as db:
        price_history = await service._real_price_history(db, identity.canonical_key)

    assert price_history["status"] == "OK"
    assert price_history["min_price"] == "299.00"
    assert price_history["max_price"] == "349.00"
    assert price_history["latest_price"] == "299.00"
    assert price_history["trend"] == "DOWN"


@pytest.mark.asyncio
async def test_connect_001_no_real_history_returns_insufficient_data_not_fabricated():
    # A product name that has (almost certainly) never been ingested. Must
    # include a recognized brand + model/storage tokens -- a name the real
    # normalizer can't detect ANY identity fields from collapses to a
    # degenerate canonical_key of just the country code ("de"), which any
    # other unrecognized-name test could also produce and collide on.
    never_seen_name = "Lenovo ThinkPad ZQ99 256GB 16GB"
    identity = ProductNormalizationService().normalize(
        ProductNormalizationInput(product_name=never_seen_name, country="DE")
    )
    assert identity.canonical_key == "lenovo::thinkpad::zq99::16gb::256gb::de"

    service = ShoppingPipelineService()
    async with AsyncSessionLocal() as db:
        price_history = await service._real_price_history(db, identity.canonical_key)

    assert price_history == {"status": "INSUFFICIENT_DATA", "reason": "PRODUCT_NOT_FOUND"}
    # The old bug's tell: a fabricated "949.00" (the hardcoded fallback)
    # anywhere in the response.
    assert "949.00" not in str(price_history)
    assert "min_price" not in price_history
    assert "max_price" not in price_history


@pytest.mark.asyncio
async def test_connect_001_missing_canonical_key_returns_insufficient_data():
    service = ShoppingPipelineService()
    async with AsyncSessionLocal() as db:
        price_history = await service._real_price_history(db, None)

    assert price_history == {"status": "INSUFFICIENT_DATA", "reason": "NO_CANONICAL_KEY"}
