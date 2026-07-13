from dataclasses import dataclass, field

from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.products.merge_repository import ProductMergeRepository


@dataclass
class PersistentMergeItemResult:
    duplicate_product_id: str
    reassigned_offer_count: int
    soft_deleted: bool
    status: str
    error: str | None = None


@dataclass
class PersistentMergeResult:
    master_product_id: str
    duplicate_count: int
    total_reassigned_offers: int
    applied: bool
    items: list[PersistentMergeItemResult] = field(default_factory=list)
    error: str | None = None


class PersistentProductMergeService:
    def __init__(self, db: AsyncSession):
        self.repo = ProductMergeRepository(db)

    async def apply_merge_plan(self, merge_plan: dict) -> PersistentMergeResult:
        master_product_id = merge_plan.get("master_product_id")
        duplicate_ids = merge_plan.get("duplicate_product_ids") or []

        if not master_product_id:
            return PersistentMergeResult(
                master_product_id="",
                duplicate_count=len(duplicate_ids),
                total_reassigned_offers=0,
                applied=False,
                error="missing_master_product_id",
            )

        if not duplicate_ids:
            return PersistentMergeResult(
                master_product_id=str(master_product_id),
                duplicate_count=0,
                total_reassigned_offers=0,
                applied=False,
                error="no_duplicate_product_ids",
            )

        master = await self.repo.get_product(master_product_id)
        if not master:
            return PersistentMergeResult(
                master_product_id=str(master_product_id),
                duplicate_count=len(duplicate_ids),
                total_reassigned_offers=0,
                applied=False,
                error="master_product_not_found",
            )

        items: list[PersistentMergeItemResult] = []
        total_reassigned = 0

        try:
            for duplicate_id in duplicate_ids:
                if str(duplicate_id) == str(master_product_id):
                    items.append(
                        PersistentMergeItemResult(
                            duplicate_product_id=str(duplicate_id),
                            reassigned_offer_count=0,
                            soft_deleted=False,
                            status="SKIPPED",
                            error="duplicate_is_master",
                        )
                    )
                    continue

                duplicate = await self.repo.get_product(duplicate_id)
                if not duplicate:
                    items.append(
                        PersistentMergeItemResult(
                            duplicate_product_id=str(duplicate_id),
                            reassigned_offer_count=0,
                            soft_deleted=False,
                            status="SKIPPED",
                            error="duplicate_product_not_found",
                        )
                    )
                    continue

                reassigned = await self.repo.reassign_offers(
                    from_product_id=duplicate_id,
                    to_product_id=master_product_id,
                )
                soft_deleted = await self.repo.soft_delete_product(duplicate_id)

                total_reassigned += reassigned
                items.append(
                    PersistentMergeItemResult(
                        duplicate_product_id=str(duplicate_id),
                        reassigned_offer_count=reassigned,
                        soft_deleted=soft_deleted,
                        status="MERGED",
                    )
                )

            await self.repo.commit()

            return PersistentMergeResult(
                master_product_id=str(master_product_id),
                duplicate_count=len(duplicate_ids),
                total_reassigned_offers=total_reassigned,
                applied=True,
                items=items,
            )
        except Exception as exc:
            await self.repo.rollback()
            return PersistentMergeResult(
                master_product_id=str(master_product_id),
                duplicate_count=len(duplicate_ids),
                total_reassigned_offers=total_reassigned,
                applied=False,
                items=items,
                error=str(exc),
            )
