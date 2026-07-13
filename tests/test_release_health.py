import pytest

from app.domains.system.release_health import ReleaseHealthService


class PassingIntegrityGuard:
    async def run(self, repo):
        class Item:
            name = "no_orphans"
            passed = True
            count = 0
            message = "ok"

        class Report:
            passed = True
            checks = [Item()]

        return Report()


class FailingIntegrityGuard:
    async def run(self, repo):
        class Item:
            name = "orphan_offers"
            passed = False
            count = 1
            message = "bad"

        class Report:
            passed = False
            checks = [Item()]

        return Report()


class DummyRepo:
    pass


@pytest.mark.asyncio
async def test_release_health_passes():
    result = await ReleaseHealthService().run(
        integrity_guard=PassingIntegrityGuard(),
        integrity_repo=DummyRepo(),
    )

    assert result.passed is True
    assert result.status == "OK"


@pytest.mark.asyncio
async def test_release_health_fails_on_integrity_failure():
    result = await ReleaseHealthService().run(
        integrity_guard=FailingIntegrityGuard(),
        integrity_repo=DummyRepo(),
    )

    assert result.passed is False
    assert result.status == "FAILED"
    assert result.failed_checks[0].name == "data_integrity"
