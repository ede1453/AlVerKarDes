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


class PassingRegressionGuard:
    async def run(self, repo):
        class Report:
            passed = True
            active_product_count = 1
            active_offer_product_count = 1
            deleted_product_count = 2
            errors = []

        return Report()


class FailingRegressionGuard:
    async def run(self, repo):
        class Report:
            passed = False
            active_product_count = 2
            active_offer_product_count = 1
            deleted_product_count = 2
            errors = ["active_products_without_active_offers"]

        return Report()


class DummyRepo:
    pass


@pytest.mark.asyncio
async def test_release_health_includes_duplicate_regression_pass():
    result = await ReleaseHealthService().run(
        integrity_guard=PassingIntegrityGuard(),
        integrity_repo=DummyRepo(),
        duplicate_regression_guard=PassingRegressionGuard(),
        duplicate_regression_repo=DummyRepo(),
    )

    assert result.passed is True
    assert any(check.name == "duplicate_product_regression" for check in result.checks)


@pytest.mark.asyncio
async def test_release_health_fails_on_duplicate_regression():
    result = await ReleaseHealthService().run(
        integrity_guard=PassingIntegrityGuard(),
        integrity_repo=DummyRepo(),
        duplicate_regression_guard=FailingRegressionGuard(),
        duplicate_regression_repo=DummyRepo(),
    )

    assert result.passed is False
    assert any(check.name == "duplicate_product_regression" for check in result.failed_checks)
