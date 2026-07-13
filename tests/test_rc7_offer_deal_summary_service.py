from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import uuid4

import pytest

from app.domains.deals.offer_deal_summary_service import OfferDealSummaryService


class Offer:
    def __init__(self, id):
        self.id = id


class Price:
    def __init__(self, amount, created_at, stock_status="in_stock"):
        self.amount = amount
        self.created_at = created_at
        self.stock_status = stock_status


class FakeMarketService:
    def __init__(self, offer, prices):
        self.offer = offer
        self.prices = prices

    async def get_offer(self, offer_id):
        if self.offer and self.offer.id == offer_id:
            return self.offer
        return None

    async def get_price_history(self, offer_id):
        return self.prices


class DummyDB:
    pass


@pytest.mark.asyncio
async def test_offer_deal_summary_service_returns_buy_summary():
    now = datetime(2026, 7, 5, tzinfo=timezone.utc)
    offer_id = uuid4()

    service = OfferDealSummaryService(DummyDB())
    service.market_service = FakeMarketService(
        Offer(offer_id),
        [
            Price(Decimal("899.00"), now - timedelta(days=20)),
            Price(Decimal("849.00"), now),
        ],
    )

    result = await service.summarize_offer(
        offer_id=offer_id,
        cross_store_min_amount=Decimal("849.00"),
        store_trust_score=95,
    )

    assert result["offer_id"] == str(offer_id)
    assert result["recommendation"] == "BUY"
    assert result["deal_score"]["decision"] == "BUY"


@pytest.mark.asyncio
async def test_offer_deal_summary_service_rejects_missing_offer():
    service = OfferDealSummaryService(DummyDB())
    service.market_service = FakeMarketService(None, [])

    with pytest.raises(ValueError, match="offer_not_found"):
        await service.summarize_offer(offer_id=uuid4())
