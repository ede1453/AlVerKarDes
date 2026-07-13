import pytest

from app.domains.products.post_merge_verifier import PostMergeVerifier


class FakeRepo:
    def __init__(self, active_offers=3, orphan_offers=0, active_duplicates=0):
        self.active_offers = active_offers
        self.orphan_offers = orphan_offers
        self.active_duplicates = active_duplicates

    async def count_active_offers_for_product(self, product_id):
        return self.active_offers

    async def count_active_offers_for_deleted_products(self):
        return self.orphan_offers

    async def count_active_products(self, product_ids):
        return self.active_duplicates


@pytest.mark.asyncio
async def test_post_merge_verifier_passes_clean_merge():
    result = await PostMergeVerifier().verify(
        repo=FakeRepo(),
        master_product_id="master",
        duplicate_product_ids=["dup"],
    )

    assert result.passed is True
    assert result.errors == []


@pytest.mark.asyncio
async def test_post_merge_verifier_detects_orphans():
    result = await PostMergeVerifier().verify(
        repo=FakeRepo(orphan_offers=1),
        master_product_id="master",
        duplicate_product_ids=["dup"],
    )

    assert result.passed is False
    assert "active_offers_reference_deleted_products" in result.errors


@pytest.mark.asyncio
async def test_post_merge_verifier_detects_active_duplicates():
    result = await PostMergeVerifier().verify(
        repo=FakeRepo(active_duplicates=1),
        master_product_id="master",
        duplicate_product_ids=["dup"],
    )

    assert result.passed is False
    assert "duplicate_products_still_active" in result.errors
