from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.domains.integrity.duplicate_product_regression import DuplicateProductRegressionGuard
from app.domains.integrity.duplicate_product_regression_repository import DuplicateProductRegressionRepository

router = APIRouter(prefix="/integrity", tags=["integrity"])


@router.get("/duplicate-product-regression")
async def duplicate_product_regression(db: AsyncSession = Depends(get_db)):
    report = await DuplicateProductRegressionGuard().run(
        DuplicateProductRegressionRepository(db)
    )

    return {
        "passed": report.passed,
        "active_product_count": report.active_product_count,
        "active_offer_product_count": report.active_offer_product_count,
        "deleted_product_count": report.deleted_product_count,
        "errors": report.errors,
    }
