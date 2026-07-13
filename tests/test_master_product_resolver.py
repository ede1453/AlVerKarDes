import pytest

from app.domains.products.master_product_resolver import MasterProductResolver


class FakeRepo:
    async def get_active_product_ids_by_offer_urls(self, urls):
        return [
            {
                "product_id": "master-product",
                "offer_count": 3,
                "canonical_key": "apple::macbook-air::m5::16gb::512gb::de",
                "canonical_quality": 12,
            }
        ]


class EmptyRepo:
    async def get_active_product_ids_by_offer_urls(self, urls):
        return []


@pytest.mark.asyncio
async def test_master_product_resolver_finds_existing_master():
    result = await MasterProductResolver().resolve_from_group(
        repo=FakeRepo(),
        group={"offers": [{"url": "https://example.com/a"}, {"url": "https://example.com/b"}]},
    )

    assert result.master_product_id == "master-product"
    assert result.confidence == 95


@pytest.mark.asyncio
async def test_master_product_resolver_returns_none_without_existing_product():
    result = await MasterProductResolver().resolve_from_group(
        repo=EmptyRepo(),
        group={"offers": [{"url": "https://example.com/unknown"}]},
    )

    assert result.master_product_id is None
    assert result.reason == "no_existing_active_product_for_group"
