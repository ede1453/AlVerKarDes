from dataclasses import dataclass, field


@dataclass
class DuplicateProductRegressionReport:
    passed: bool
    active_product_count: int
    active_offer_product_count: int
    deleted_product_count: int
    errors: list[str] = field(default_factory=list)


class DuplicateProductRegressionGuard:
    async def run(self, repo) -> DuplicateProductRegressionReport:
        active_product_count = await repo.count_active_products()
        active_offer_product_count = await repo.count_distinct_active_offer_products()
        deleted_product_count = await repo.count_deleted_products()

        errors: list[str] = []

        if active_offer_product_count > active_product_count:
            errors.append("offers_reference_more_products_than_active_products")

        if active_product_count > active_offer_product_count and active_offer_product_count > 0:
            errors.append("active_products_without_active_offers")

        return DuplicateProductRegressionReport(
            passed=not errors,
            active_product_count=active_product_count,
            active_offer_product_count=active_offer_product_count,
            deleted_product_count=deleted_product_count,
            errors=errors,
        )
