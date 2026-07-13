import pytest

from app.domains.integrity.duplicate_product_regression import DuplicateProductRegressionGuard


class FakeRepo:
    def __init__(self, active_products=1, active_offer_products=1, deleted_products=1):
        self.active_products = active_products
        self.active_offer_products = active_offer_products
        self.deleted_products = deleted_products

    async def count_active_products(self):
        return self.active_products

    async def count_distinct_active_offer_products(self):
        return self.active_offer_products

    async def count_deleted_products(self):
        return self.deleted_products


@pytest.mark.asyncio
async def test_duplicate_product_regression_passes_clean_graph():
    report = await DuplicateProductRegressionGuard().run(FakeRepo())

    assert report.passed is True
    assert report.errors == []


@pytest.mark.asyncio
async def test_duplicate_product_regression_detects_active_product_without_offers():
    report = await DuplicateProductRegressionGuard().run(
        FakeRepo(active_products=2, active_offer_products=1)
    )

    assert report.passed is False
    assert "active_products_without_active_offers" in report.errors
