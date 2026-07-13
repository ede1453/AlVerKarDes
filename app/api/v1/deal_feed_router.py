from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.domains.deal_feed.service import (
    DealFeedService,
)

router = APIRouter(
    prefix="/deal-feed",
    tags=["deal-feed"],
)

_service = DealFeedService()


class DealIngestRequest(BaseModel):
    deals: list[dict[str, Any]] = Field(
        default_factory=list
    )


class FeedRequest(BaseModel):
    preferences: dict[str, Any] = Field(
        default_factory=dict
    )
    minimum_confidence: float = 0
    limit: int = 50


@router.post("/clear")
def clear_deal_feed():
    return _service.clear()


@router.post("/ingest")
def ingest_deals(
    payload: DealIngestRequest,
):
    return _service.ingest_deals(
        deals=payload.deals
    )


@router.post("/query")
def query_deal_feed(
    payload: FeedRequest,
):
    return _service.get_feed(
        **payload.model_dump()
    )


@router.get("/deals/{deal_id}")
def get_deal(deal_id: str):
    deal = _service.get_deal(deal_id)

    if deal is None:
        raise HTTPException(
            status_code=404,
            detail="DEAL_NOT_FOUND",
        )

    return deal
