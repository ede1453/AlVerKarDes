import pytest

from app.domains.products.persistent_merge_service import PersistentProductMergeService


class DummyProduct:
    def __init__(self, id):
        self.id = id


class FakeRepo:
    def __init__(self):
        self.products = {
            "master": DummyProduct("master"),
            "dup": DummyProduct("dup"),
        }
        self.reassigned = []
        self.deleted = []
        self.committed = False
        self.rolled_back = False

    async def get_product(self, product_id):
        return self.products.get(str(product_id))

    async def reassign_offers(self, *, from_product_id, to_product_id):
        self.reassigned.append((str(from_product_id), str(to_product_id)))
        return 2

    async def soft_delete_product(self, product_id):
        self.deleted.append(str(product_id))
        return True

    async def commit(self):
        self.committed = True

    async def rollback(self):
        self.rolled_back = True


@pytest.mark.asyncio
async def test_persistent_merge_applies_plan(monkeypatch):
    service = PersistentProductMergeService(db=None)
    fake_repo = FakeRepo()
    service.repo = fake_repo

    result = await service.apply_merge_plan({
        "master_product_id": "master",
        "duplicate_product_ids": ["dup"],
    })

    assert result.applied is True
    assert result.total_reassigned_offers == 2
    assert result.items[0].status == "MERGED"
    assert fake_repo.reassigned == [("dup", "master")]
    assert fake_repo.deleted == ["dup"]
    assert fake_repo.committed is True


@pytest.mark.asyncio
async def test_persistent_merge_rejects_missing_master():
    service = PersistentProductMergeService(db=None)
    service.repo = FakeRepo()

    result = await service.apply_merge_plan({
        "duplicate_product_ids": ["dup"],
    })

    assert result.applied is False
    assert result.error == "missing_master_product_id"


@pytest.mark.asyncio
async def test_persistent_merge_skips_duplicate_is_master():
    service = PersistentProductMergeService(db=None)
    service.repo = FakeRepo()

    result = await service.apply_merge_plan({
        "master_product_id": "master",
        "duplicate_product_ids": ["master"],
    })

    assert result.applied is True
    assert result.items[0].status == "SKIPPED"
    assert result.items[0].error == "duplicate_is_master"
