import pytest


class DummyPrice:
    def __init__(self, amount):
        self.amount = amount


class FakePriceRepo:
    async def latest_for_offer(self, offer_id):
        return DummyPrice(849)

    async def list_for_offer(self, offer_id, limit=None):
        return [DummyPrice(999), DummyPrice(849)]


class FakeOfferRepo:
    async def get_by_id(self, offer_id):
        return {"id": str(offer_id)}


@pytest.mark.asyncio
async def test_market_service_latest_price_compatibility():
    from app.domains.market.service import MarketService

    service = MarketService(db=None)
    service.price_repo = FakePriceRepo()
    service.offer_repo = FakeOfferRepo()

    latest = await service.get_latest_price_point("offer-1")

    assert latest.amount == 849


@pytest.mark.asyncio
async def test_market_service_price_history_compatibility():
    from app.domains.market.service import MarketService

    service = MarketService(db=None)
    service.price_repo = FakePriceRepo()
    service.offer_repo = FakeOfferRepo()

    history = await service.get_price_history("offer-1")

    assert len(history) == 2
    assert history[-1].amount == 849
