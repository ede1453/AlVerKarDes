from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.domains.watchlist.watchlist_service import WatchlistService


class WatchlistAddRequest(BaseModel):
    user_id: str
    product_key: str
    query: str
    target_price: str | None = None
    marketplaces: list[str] = Field(default_factory=list)
    channels: list[str] = Field(default_factory=lambda: ["in_app"])
    metadata: dict = Field(default_factory=dict)


class WatchlistEvaluateRequest(BaseModel):
    deal_detection: dict | None = None
    price_prediction: dict | None = None
    personalization: dict | None = None
    price_history: dict | None = None


router = APIRouter(prefix="/watchlist", tags=["watchlist"])

_service = WatchlistService()


@router.post("/items")
async def add_watchlist_item(payload: WatchlistAddRequest):
    return _service.add_item(payload.model_dump())


@router.get("/users/{user_id}/items")
async def list_watchlist_items(user_id: str):
    return {"items": _service.list_for_user(user_id)}


@router.get("/items/{item_id}")
async def get_watchlist_item(item_id: str):
    item = _service.get_item(item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="watchlist_item_not_found")
    return item


@router.post("/items/{item_id}/evaluate")
async def evaluate_watchlist_item(item_id: str, payload: WatchlistEvaluateRequest):
    item = _service.evaluate_item(item_id, payload.model_dump())
    if item is None:
        raise HTTPException(status_code=404, detail="watchlist_item_not_found")
    return item


@router.post("/items/{item_id}/deactivate")
async def deactivate_watchlist_item(item_id: str):
    item = _service.deactivate_item(item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="watchlist_item_not_found")
    return item


@router.post("/clear")
async def clear_watchlist():
    return _service.clear()
