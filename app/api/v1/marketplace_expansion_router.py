from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.domains.commerce_ingestion.marketplace_connectors import (
    MarketplaceConnectorError,
    MarketplaceConnectorFactory,
    MarketplaceScoreEngine,
)

router = APIRouter(prefix="/marketplace-expansion", tags=["marketplace-expansion"])

class NormalizeRequest(BaseModel):
    marketplace: str
    item: dict[str, Any] = Field(default_factory=dict)

class NormalizeBatchRequest(BaseModel):
    marketplace: str
    items: list[dict[str, Any]] = Field(default_factory=list)

class ScoreRequest(BaseModel):
    current_price: float
    historical_average_price: float | None = None
    store_trust_score: int
    availability: str
    shipping_cost: float = 0.0
    review_score: float | None = None

@router.post("/normalize")
def normalize_item(payload: NormalizeRequest):
    try:
        connector = MarketplaceConnectorFactory.create(payload.marketplace)
    except MarketplaceConnectorError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"normalized": True, "item": connector.normalize(payload.item)}

@router.post("/normalize-batch")
def normalize_batch(payload: NormalizeBatchRequest):
    try:
        connector = MarketplaceConnectorFactory.create(payload.marketplace)
    except MarketplaceConnectorError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    items = [connector.normalize(item) for item in payload.items]
    return {"normalized": True, "item_count": len(items), "items": items}

@router.post("/score")
def score_offer(payload: ScoreRequest):
    return MarketplaceScoreEngine().calculate(**payload.model_dump())
