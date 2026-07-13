import pytest


class DummyOffer:
    def __init__(self, id, url):
        self.id = id
        self.url = url


class FakeOfferRepo:
    def __init__(self):
        self.by_url = {}
        self.created_count = 0

    async def get_by_url(self, url: str):
        return self.by_url.get(url)

    async def create(self, payload):
        self.created_count += 1
        offer = DummyOffer(f"offer-{self.created_count}", payload.url)
        self.by_url[payload.url] = offer
        return offer


class DummyPayload:
    def __init__(self, url):
        self.url = url


@pytest.mark.asyncio
async def test_get_or_create_offer_reuses_url():
    from app.domains.market.service import MarketService

    service = MarketService(db=None)
    repo = FakeOfferRepo()
    service.offer_repo = repo

    first, first_created = await service.get_or_create_offer(DummyPayload("https://example.com/a"))
    second, second_created = await service.get_or_create_offer(DummyPayload("https://example.com/a"))

    assert first.id == second.id
    assert first_created is True
    assert second_created is False
    assert repo.created_count == 1
