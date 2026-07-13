import pytest

from app.domains.products.orphan_cleanup import OrphanProductCleanupService
from app.domains.products.persistent_merge_service import PersistentProductMergeService


class DummyProduct:
    def __init__(self, id):
        self.id = id


class IdempotentMergeRepo:
    def __init__(self):
        self.products = {
            "master": DummyProduct("master"),
            "dup": DummyProduct("dup"),
        }
        self.merged_once = False
        self.deleted = set()
        self.commits = 0

    async def get_product(self, product_id):
        if str(product_id) in self.deleted:
            return None
        return self.products.get(str(product_id))

    async def reassign_offers(self, *, from_product_id, to_product_id):
        if self.merged_once:
            return 0
        self.merged_once = True
        return 2

    async def soft_delete_product(self, product_id):
        if str(product_id) in self.deleted:
            return False
        self.deleted.add(str(product_id))
        return True

    async def commit(self):
        self.commits += 1

    async def rollback(self):
        pass


@pytest.mark.asyncio
async def test_persistent_merge_is_safe_when_repeated():
    repo = IdempotentMergeRepo()
    service = PersistentProductMergeService(db=None)
    service.repo = repo

    payload = {
        "master_product_id": "master",
        "duplicate_product_ids": ["dup"],
    }

    first = await service.apply_merge_plan(payload)
    second = await service.apply_merge_plan(payload)

    assert first.applied is True
    assert first.total_reassigned_offers == 2

    assert second.applied is True
    assert second.total_reassigned_offers == 0
    assert second.items[0].status == "SKIPPED"
    assert second.items[0].error == "duplicate_product_not_found"


class IdempotentCleanupRepo:
    def __init__(self):
        self.orphans = ["orphan"]
        self.cleaned = False
        self.commits = 0

    async def list_active_product_ids_without_active_offers(self):
        return [] if self.cleaned else self.orphans

    async def soft_delete_product(self, product_id):
        self.cleaned = True
        return True

    async def commit(self):
        self.commits += 1


@pytest.mark.asyncio
async def test_orphan_cleanup_is_safe_when_repeated():
    repo = IdempotentCleanupRepo()
    service = OrphanProductCleanupService()

    first = await service.run(repo, dry_run=False)
    second = await service.run(repo, dry_run=False)

    assert first.found_count == 1
    assert first.cleaned_count == 1

    assert second.found_count == 0
    assert second.cleaned_count == 0
