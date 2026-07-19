from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.domains.products.post_merge_repository import PostMergeVerificationRepository
from app.domains.products.post_merge_verifier import PostMergeVerifier
from app.domains.identity.dependencies import get_current_user, require_role
from app.domains.identity.models import UserRole

router = APIRouter(prefix="/products/merge", tags=["products-merge"])


class VerifyMergeRequest(BaseModel):
    master_product_id: str
    duplicate_product_ids: list[str]


@router.post("/verify")
async def verify_merge(
    payload: VerifyMergeRequest,
    db: AsyncSession = Depends(get_db),
    # AUTH-006 Parça 3 (ADR-005): OPERATOR+ gerektirir.
    current_user=Depends(require_role(UserRole.OPERATOR)),
):
    repo = PostMergeVerificationRepository(db)
    result = await PostMergeVerifier().verify(
        repo=repo,
        master_product_id=payload.master_product_id,
        duplicate_product_ids=payload.duplicate_product_ids,
    )

    return {
        "master_product_id": result.master_product_id,
        "duplicate_product_ids": result.duplicate_product_ids,
        "active_offer_count_for_master": result.active_offer_count_for_master,
        "orphan_offer_count": result.orphan_offer_count,
        "duplicate_active_product_count": result.duplicate_active_product_count,
        "passed": result.passed,
        "errors": result.errors,
    }
