from dataclasses import dataclass, field


@dataclass
class PostMergeVerificationResult:
    master_product_id: str
    duplicate_product_ids: list[str]
    active_offer_count_for_master: int
    orphan_offer_count: int
    duplicate_active_product_count: int
    passed: bool
    errors: list[str] = field(default_factory=list)


class PostMergeVerifier:
    async def verify(self, *, repo, master_product_id: str, duplicate_product_ids: list[str]) -> PostMergeVerificationResult:
        errors: list[str] = []

        active_offer_count = await repo.count_active_offers_for_product(master_product_id)
        orphan_offer_count = await repo.count_active_offers_for_deleted_products()
        duplicate_active_count = await repo.count_active_products(duplicate_product_ids)

        if active_offer_count < 1:
            errors.append("master_product_has_no_active_offers")

        if orphan_offer_count > 0:
            errors.append("active_offers_reference_deleted_products")

        if duplicate_active_count > 0:
            errors.append("duplicate_products_still_active")

        return PostMergeVerificationResult(
            master_product_id=master_product_id,
            duplicate_product_ids=duplicate_product_ids,
            active_offer_count_for_master=active_offer_count,
            orphan_offer_count=orphan_offer_count,
            duplicate_active_product_count=duplicate_active_count,
            passed=not errors,
            errors=errors,
        )
