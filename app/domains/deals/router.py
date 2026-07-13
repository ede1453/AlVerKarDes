from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.domains.deals.deal_summary_schemas import (
    DealSummaryRequest,
    DealSummaryResponse,
)
from app.domains.deals.deal_summary_service import DealSummaryService
from app.domains.deals.offer_deal_summary_schemas import OfferDealSummaryResponse
from app.domains.deals.offer_deal_summary_service import OfferDealSummaryService

router = APIRouter(prefix="/deals", tags=["deals"])


@router.post("/summary", response_model=DealSummaryResponse)
async def build_deal_summary(payload: DealSummaryRequest):
    return DealSummaryService().summarize(
        prices=[item.model_dump() for item in payload.prices],
        cross_store_min_amount=payload.cross_store_min_amount,
        store_trust_score=payload.store_trust_score,
        stock_status=payload.stock_status,
    )

@router.get("/offers/{offer_id}/summary", response_model=OfferDealSummaryResponse)
async def build_offer_deal_summary(
    offer_id: UUID,
    cross_store_min_amount: Decimal | None = Query(default=None),
    store_trust_score: float | None = Query(default=None),
    stock_status: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await OfferDealSummaryService(db).summarize_offer(
            offer_id=offer_id,
            cross_store_min_amount=cross_store_min_amount,
            store_trust_score=store_trust_score,
            stock_status=stock_status,
        )
    except ValueError as exc:
        error = str(exc)
        if error == "offer_not_found":
            raise HTTPException(status_code=404, detail=error) from exc
        raise HTTPException(status_code=400, detail=error) from exc