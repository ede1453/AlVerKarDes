import pytest

from app.domains.products.orphan_cleanup import OrphanProductCleanupService


class FakeRepo:
    def __init__(self):
        self.orphans = ["product-orphan"]
        self.deleted = []
        self.committed = False

    async def list_active_product_ids_without_active_offers(self):
        return self.orphans

    async def soft_delete_product(self, product_id):
        self.deleted.append(product_id)
        return True

    async def commit(self):
        self.committed = True


@pytest.mark.asyncio
async def test_orphan_cleanup_dry_run():
    repo = FakeRepo()

    result = await OrphanProductCleanupService().run(repo, dry_run=True)

    assert result.found_count == 1
    assert result.cleaned_count == 0
    assert repo.deleted == []


@pytest.mark.asyncio
async def test_orphan_cleanup_applies():
    repo = FakeRepo()

    result = await OrphanProductCleanupService().run(repo, dry_run=False)

    assert result.found_count == 1
    assert result.cleaned_count == 1
    assert repo.deleted == ["product-orphan"]
    assert repo.committed is True
