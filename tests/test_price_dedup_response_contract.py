from decimal import Decimal

import pytest

from app.domains.market.schemas import PriceSnapshotCreate
from app.domains.market.service import MarketService


class Price:
    def __init__(self, id="price-1", amount=Decimal("849.00"), currency="EUR", stock_status="in_stock"):
        self.id = id
        self.amount = amount
        self.currency = currency
        self.stock_status = stock_status


class FakePriceRepo:
    def __init__(self):
        self.latest = None
        self.created_count = 0

    async def latest_for_offer(self, offer_id):
        return self.latest

    async def create(self, payload):
        self.created_count += 1
        self.latest = Price(
            id=f"price-{self.created_count}",
            amount=payload.amount,
            currency=payload.currency,
            stock_status=payload.stock_status,
        )
        return self.latest


class DummyDB:
    pass


@pytest.mark.asyncio
async def test_save_price_snapshot_marks_created_price():
    service = MarketService(DummyDB())
    service.price_repo = FakePriceRepo()

    price = await service.save_price_snapshot(
        PriceSnapshotCreate(
            offer_id="11111111-1111-1111-1111-111111111111",
            amount=Decimal("849.00"),
            currency="EUR",
            stock_status="in_stock",
        )
    )

    assert price._price_created is True
    assert price._price_dedup_reason == "no_previous_price"


@pytest.mark.asyncio
async def test_save_price_snapshot_marks_deduped_price():
    service = MarketService(DummyDB())
    service.price_repo = FakePriceRepo()
    service.price_repo.latest = Price()

    price = await service.save_price_snapshot(
        PriceSnapshotCreate(
            offer_id="11111111-1111-1111-1111-111111111111",
            amount=Decimal("849.00"),
            currency="EUR",
            stock_status="in_stock",
        )
    )

    assert price._price_created is False
    assert price._price_dedup_reason == "duplicate_price_snapshot"
    assert service.price_repo.created_count == 0
