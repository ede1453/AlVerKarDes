from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.domains.products.persistent_merge_service import PersistentProductMergeService
from app.domains.identity.dependencies import get_current_user, require_role
from app.domains.identity.models import UserRole

router = APIRouter(prefix="/products/merge", tags=["products-merge"])


class ApplyMergePlanRequest(BaseModel):
    merge_plan: dict


@router.post("/apply")
async def apply_merge_plan(
    payload: ApplyMergePlanRequest,
    db: AsyncSession = Depends(get_db),
    # AUTH-006 Parça 3 (ADR-005): OPERATOR+ gerektirir.
    current_user=Depends(require_role(UserRole.OPERATOR)),
):
    result = await PersistentProductMergeService(db).apply_merge_plan(payload.merge_plan)
    return {
        "master_product_id": result.master_product_id,
        "duplicate_count": result.duplicate_count,
        "total_reassigned_offers": result.total_reassigned_offers,
        "applied": result.applied,
        "items": [item.__dict__ for item in result.items],
        "error": result.error,
    }
