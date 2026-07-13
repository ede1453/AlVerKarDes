from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.domains.products.orphan_cleanup import OrphanProductCleanupService
from app.domains.products.orphan_cleanup_repository import OrphanProductCleanupRepository

router = APIRouter(prefix="/products/cleanup", tags=["products-cleanup"])


@router.post("/orphans")
async def cleanup_orphan_products(dry_run: bool = True, db: AsyncSession = Depends(get_db)):
    result = await OrphanProductCleanupService().run(
        OrphanProductCleanupRepository(db),
        dry_run=dry_run,
    )

    return {
        "found_count": result.found_count,
        "cleaned_count": result.cleaned_count,
        "cleaned_product_ids": result.cleaned_product_ids,
        "dry_run": result.dry_run,
    }
