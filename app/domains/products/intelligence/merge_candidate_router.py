from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.domains.products.intelligence.merge_candidate_api_schemas import (
    MergeCandidateRequest,
    MergeCandidateResponse,
)
from app.domains.products.intelligence.merge_candidate_apply_service import MergeCandidateApplyService
from app.domains.products.intelligence.merge_candidate_persistence_service import MergeCandidatePersistenceService
from app.domains.products.intelligence.merge_candidate_repository import MergeCandidateRepository
from app.domains.products.intelligence.merge_candidate_review_schemas import (
    MergeCandidateReviewRequest,
    MergeCandidateReviewResponse,
)
from app.domains.products.intelligence.merge_candidate_review_service import MergeCandidateReviewService
from app.domains.products.intelligence.merge_candidate_service import MergeCandidateService

router = APIRouter(prefix="/products/intelligence", tags=["products-intelligence"])


@router.post("/merge-candidates", response_model=MergeCandidateResponse)
async def build_merge_candidates(payload: MergeCandidateRequest):
    return MergeCandidateService().build_from_offers(
        offers=[item.model_dump() for item in payload.offers],
        country=payload.country,
    )

@router.post("/merge-candidates/persist")
async def persist_merge_candidates(
    payload: MergeCandidateRequest,
    db: AsyncSession = Depends(get_db),
):
    return await MergeCandidatePersistenceService(db).build_and_persist(
        offers=[item.model_dump() for item in payload.offers],
        country=payload.country,
    )

@router.patch(
    "/merge-candidates/{candidate_id}/review",
    response_model=MergeCandidateReviewResponse,
)
async def review_merge_candidate(
    candidate_id: UUID,
    payload: MergeCandidateReviewRequest,
    db: AsyncSession = Depends(get_db),
):
    try:
        return await MergeCandidateReviewService(
            MergeCandidateRepository(db)
        ).review(
            candidate_id=candidate_id,
            status=payload.status,
        )
    except ValueError as exc:
        error = str(exc)
        if error == "merge_candidate_not_found":
            raise HTTPException(status_code=404, detail=error) from exc
        raise HTTPException(status_code=400, detail=error) from exc
   
@router.post("/merge-candidates/{candidate_id}/apply")
async def apply_merge_candidate(
    candidate_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    try:
        return await MergeCandidateApplyService(
            MergeCandidateRepository(db)
        ).apply(candidate_id=candidate_id)
    except ValueError as exc:
        error = str(exc)
        if error == "merge_candidate_not_found":
            raise HTTPException(status_code=404, detail=error) from exc
        raise HTTPException(status_code=400, detail=error) from exc