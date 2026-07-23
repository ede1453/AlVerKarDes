"""VISION-000 (ADR-018): decision_memory's first real (non-test-fixture)
consumer. Before this, decision_memory had zero real usage -- nothing wrote
to it except manual `POST /decision-memory/store` calls, which no domain and
no frontend ever made (verified by grep before writing this slice). This
wires the one live, DB-backed, user-scoped decision path
(`shopping_pipeline.run()`) to actually record decisions and read back a
plain recency summary (count-by-decision, no embeddings/semantic search --
deliberately out of scope, see ADR-018) as context for the next call.

Deliberately a single test-suite run, not the 3-consecutive-runs discipline
used for the SCALE-0xx series: this is not a concurrency claim (no shared
mutable state being raced over), just a plain read/write/isolation check.

Test functions that use TestClient stay plain `def` (not async) and use a
throwaway engine + asyncio.run() for DB assertions, same convention as
tests/auth_test_helpers.py::_promote_role -- mixing an async test function
with TestClient's own internal event-loop portal is the exact
"another operation is in progress" failure mode that helper's docstring
warns about.
"""

import asyncio
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.domains.decision_memory.decision_memory_repository import DecisionMemoryRepository
from app.domains.market.schemas import OfferCreate, PriceSnapshotCreate, StoreCreate
from app.domains.market.service import MarketService
from app.domains.products.service import ProductService
from app.domains.shopping_pipeline.pipeline_service import ShoppingPipelineService
from app.main import app
from tests.auth_test_helpers import auth_headers_and_user_id


async def _ingest_searchable_product_async(product_name: str, price: str) -> None:
    engine = create_async_engine(settings.DATABASE_URL)
    try:
        from sqlalchemy.ext.asyncio import AsyncSession

        async with AsyncSession(engine) as db:
            product, _identity, _created = await ProductService(db).create_from_name(product_name, country="DE")
            product_id = product.id

        async with AsyncSession(engine) as db:
            market = MarketService(db)
            store = await market.create_store(
                StoreCreate(
                    name="VISION-000 Test Store",
                    slug=f"vision-000-{uuid.uuid4().hex[:8]}",
                    country="DE",
                )
            )
            offer, _ = await market.get_or_create_offer(
                OfferCreate(
                    product_id=product_id,
                    store_id=store.id,
                    url=f"https://example.com/vision-000-{uuid.uuid4().hex[:8]}",
                )
            )
            await market.save_price_snapshot(PriceSnapshotCreate(offer_id=offer.id, amount=price, currency="EUR"))
    finally:
        await engine.dispose()


def _ingest_searchable_product(product_name: str, price: str) -> None:
    asyncio.run(_ingest_searchable_product_async(product_name, price))


def _decision_memory_row_count(user_id: str) -> int:
    async def _do() -> int:
        engine = create_async_engine(settings.DATABASE_URL)
        try:
            async with engine.begin() as conn:
                result = await conn.execute(
                    text("SELECT count(*) FROM decision_memory WHERE user_id = :user_id"),
                    {"user_id": user_id},
                )
                return result.scalar_one()
        finally:
            await engine.dispose()

    return asyncio.run(_do())


def _run_pipeline(client: TestClient, headers: dict, user_id: str, query: str):
    response = client.post(
        "/api/v1/shopping-pipeline/run",
        headers=headers,
        json={"user_id": user_id, "query": query},
    )
    assert response.status_code == 200, response.text
    return response.json()


def test_authenticated_user_writes_real_decisions_and_summary_reflects_only_past_ones():
    product_name = f"VISION000 Widget Pro {uuid.uuid4().hex[:8]}"
    _ingest_searchable_product(product_name, price="199.00")

    # A single TestClient context for the whole test -- opening a second one
    # after closing the first re-triggers the same "event loop is closed"
    # failure mode auth_test_helpers.py::_promote_role's docstring warns
    # about (the shared DB engine's pooled connections stay bound to the
    # first portal's now-closed loop).
    with TestClient(app) as client:
        headers, user_id = auth_headers_and_user_id(client)

        first = _run_pipeline(client, headers, user_id, product_name)
        second = _run_pipeline(client, headers, user_id, product_name)
        third = _run_pipeline(client, headers, user_id, product_name)
        fourth = _run_pipeline(client, headers, user_id, product_name)

    # First 3 calls: each reads a summary of *earlier* calls only (read
    # happens before this run's own decision is written).
    assert first["explanation"]["user_decision_history"]["total"] == 0
    assert second["explanation"]["user_decision_history"]["total"] == 1
    assert third["explanation"]["user_decision_history"]["total"] == 2

    summary = fourth["explanation"]["user_decision_history"]
    assert summary["total"] == 3
    assert summary["most_recent_decision"] in {"BUY_NOW", "CONSIDER"}
    assert sum(summary["counts_by_decision"].values()) == 3

    assert _decision_memory_row_count(user_id) == 4


def test_anonymous_call_is_rejected_and_writes_no_row():
    probe_user_id = str(uuid.uuid4())
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/shopping-pipeline/run",
            json={"user_id": probe_user_id, "query": "anonymous probe query"},
        )
    assert response.status_code == 401
    assert _decision_memory_row_count(probe_user_id) == 0


@pytest.mark.asyncio
async def test_direct_service_call_without_authenticated_user_id_skips_decision_memory_write():
    # Defensive-design check independent of the HTTP layer: even if
    # ShoppingPipelineService.run() were ever reachable without going through
    # the router's get_current_user guard, omitting authenticated_user_id
    # must silently skip the decision_memory write (never raise, never write
    # under a fabricated/spoofed identity). No TestClient here, so the shared
    # AsyncSessionLocal engine is safe to use directly (same pattern as the
    # CONNECT-001 tests).
    product_name = f"VISION000 Anon Widget {uuid.uuid4().hex[:8]}"
    await _ingest_searchable_product_async(product_name, price="149.00")

    fake_user_id = str(uuid.uuid4())

    service = ShoppingPipelineService()
    async with AsyncSessionLocal() as db:
        result = await service.run({"user_id": fake_user_id, "query": product_name}, db)

    assert result["explanation"]["user_decision_history"] is None

    async with AsyncSessionLocal() as db:
        records = await DecisionMemoryRepository(db).list_recent_by_user(fake_user_id, limit=10)
    assert records == []


def test_cross_user_history_does_not_leak():
    product_name = f"VISION000 CrossUser Widget {uuid.uuid4().hex[:8]}"
    _ingest_searchable_product(product_name, price="89.00")

    with TestClient(app) as client:
        headers_a, user_a = auth_headers_and_user_id(client)
        headers_b, user_b = auth_headers_and_user_id(client)

        # User A builds up 2 real decisions.
        _run_pipeline(client, headers_a, user_a, product_name)
        _run_pipeline(client, headers_a, user_a, product_name)

        # User B's very first call must see an empty history -- not A's.
        b_first = _run_pipeline(client, headers_b, user_b, product_name)

    assert b_first["explanation"]["user_decision_history"]["total"] == 0
    assert b_first["explanation"]["user_decision_history"]["counts_by_decision"] == {}

    assert _decision_memory_row_count(user_a) == 2
    assert _decision_memory_row_count(user_b) == 1
