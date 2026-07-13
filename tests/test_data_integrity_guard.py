import pytest

from app.domains.integrity.data_integrity_guard import DataIntegrityGuard


class FakeRepo:
    def __init__(self, orphan_offers=0, duplicate_keys=0):
        self.orphan_offers = orphan_offers
        self.duplicate_keys = duplicate_keys

    async def count_active_offers_for_deleted_products(self):
        return self.orphan_offers

    async def count_duplicate_active_canonical_keys(self):
        return self.duplicate_keys


@pytest.mark.asyncio
async def test_data_integrity_guard_passes_clean_state():
    report = await DataIntegrityGuard().run(FakeRepo())

    assert report.passed is True
    assert report.failed_checks == []


@pytest.mark.asyncio
async def test_data_integrity_guard_detects_orphan_offers():
    report = await DataIntegrityGuard().run(FakeRepo(orphan_offers=1))

    assert report.passed is False
    assert report.failed_checks[0].name == "active_offers_do_not_reference_deleted_products"


@pytest.mark.asyncio
async def test_data_integrity_guard_detects_duplicate_keys():
    report = await DataIntegrityGuard().run(FakeRepo(duplicate_keys=1))

    assert report.passed is False
    assert any(check.name == "no_duplicate_active_canonical_keys" for check in report.failed_checks)
