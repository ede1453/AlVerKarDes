from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.domains.identity.dependencies import ensure_owner, get_current_user, require_role
from app.domains.identity.models import UserRole
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
async def add_watchlist_item(
    payload: WatchlistAddRequest,
    current_user=Depends(get_current_user),
):
    ensure_owner(current_user, payload.user_id)
    return _service.add_item(payload.model_dump())


@router.get("/users/{user_id}/items")
async def list_watchlist_items(
    user_id: str,
    current_user=Depends(get_current_user),
):
    ensure_owner(current_user, user_id)
    return {"items": _service.list_for_user(user_id)}


@router.get("/items/{item_id}")
async def get_watchlist_item(
    item_id: str,
    current_user=Depends(get_current_user),
):
    item = _service.get_item(item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="watchlist_item_not_found")
    ensure_owner(current_user, item["user_id"])
    return item


@router.post("/items/{item_id}/evaluate")
async def evaluate_watchlist_item(
    item_id: str,
    payload: WatchlistEvaluateRequest,
    current_user=Depends(get_current_user),
):
    item = _service.get_item(item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="watchlist_item_not_found")
    ensure_owner(current_user, item["user_id"])
    item = _service.evaluate_item(item_id, payload.model_dump())
    if item is None:
        raise HTTPException(status_code=404, detail="watchlist_item_not_found")
    return item


@router.post("/items/{item_id}/deactivate")
async def deactivate_watchlist_item(
    item_id: str,
    current_user=Depends(get_current_user),
):
    item = _service.get_item(item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="watchlist_item_not_found")
    ensure_owner(current_user, item["user_id"])
    item = _service.deactivate_item(item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="watchlist_item_not_found")
    return item


@router.post("/clear")
async def clear_watchlist(
    # AUTH-006 Parça 3 (ADR-005): OPERATOR+ gerektirir.
    current_user=Depends(require_role(UserRole.OPERATOR)),
):
    return _service.clear()
