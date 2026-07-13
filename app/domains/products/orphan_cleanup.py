from dataclasses import dataclass, field


@dataclass
class OrphanProductCleanupResult:
    found_count: int
    cleaned_count: int
    cleaned_product_ids: list[str] = field(default_factory=list)
    dry_run: bool = True


class OrphanProductCleanupService:
    async def run(self, repo, *, dry_run: bool = True) -> OrphanProductCleanupResult:
        orphan_ids = await repo.list_active_product_ids_without_active_offers()

        cleaned: list[str] = []

        if not dry_run:
            for product_id in orphan_ids:
                ok = await repo.soft_delete_product(product_id)
                if ok:
                    cleaned.append(str(product_id))

            await repo.commit()

        return OrphanProductCleanupResult(
            found_count=len(orphan_ids),
            cleaned_count=len(cleaned),
            cleaned_product_ids=cleaned,
            dry_run=dry_run,
        )
