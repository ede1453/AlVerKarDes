from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.domains.deal_operations.service import (
    DealDecisionOperationsService,
)

router = APIRouter(
    prefix="/deal-operations",
    tags=["deal-operations"],
)

_service = DealDecisionOperationsService()


class EvaluateRequest(BaseModel):
    opportunities: list[dict[str, Any]] = Field(
        default_factory=list
    )
    user_id: str | None = None


class WatchlistRequest(BaseModel):
    user_id: str
    product_key: str
    target_price: float | None = None
    minimum_confidence: float = 60


@router.post("/clear")
def clear_deal_operations():
    global _service
    _service = DealDecisionOperationsService()
    return {"cleared": True}


@router.post("/watchlist")
def add_watchlist_item(
    payload: WatchlistRequest,
):
    return _service.repository.add_watchlist_item(
        **payload.model_dump()
    )


@router.get("/watchlist")
def list_watchlist(
    user_id: str | None = None,
    active: bool | None = None,
):
    items = _service.repository.list_watchlist(
        user_id=user_id,
        active=active,
    )

    return {
        "watch_count": len(items),
        "items": items,
    }


@router.post("/evaluate")
def evaluate_and_store(
    payload: EvaluateRequest,
):
    return _service.evaluate_and_store(
        opportunities=payload.opportunities,
        user_id=payload.user_id,
    )


@router.get(
    "/opportunities/{opportunity_id}"
)
def get_opportunity(
    opportunity_id: str,
):
    opportunity = (
        _service.repository.get_opportunity(
            opportunity_id
        )
    )

    if opportunity is None:
        raise HTTPException(
            status_code=404,
            detail="OPPORTUNITY_NOT_FOUND",
        )

    return opportunity


@router.get(
    "/opportunities/{opportunity_id}/decisions"
)
def get_decision_history(
    opportunity_id: str,
):
    decisions = (
        _service.repository.get_decision_history(
            opportunity_id
        )
    )

    return {
        "decision_count": len(decisions),
        "decisions": decisions,
    }
