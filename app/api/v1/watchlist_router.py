from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.domains.billing.db_models import SubscriptionTier
from app.domains.billing.repository import SubscriptionDBRepository
from app.domains.billing.service import SubscriptionService
from app.domains.identity.dependencies import ensure_owner, get_current_user, require_role
from app.domains.identity.models import UserRole
from app.domains.watchlist.watchlist_repository import WatchlistItemDBRepository
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


def _service(db: AsyncSession) -> WatchlistService:
    # CLIENT-002e: Postgres-backed now (WatchlistItemDBRepository) -- same
    # per-request construction pattern as DecisionMemoryRepository
    # (AUTH-006 Part 2, see app/api/v1/decision_memory_router.py). No more
    # module-level singleton: a shared instance can't hold a request-scoped
    # AsyncSession.
    return WatchlistService(repository=WatchlistItemDBRepository(db))


@router.post("/items")
async def add_watchlist_item(
    payload: WatchlistAddRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    ensure_owner(current_user, payload.user_id)

    # BILL-001: FREE tier watchlist cap. Only ACTIVE items count -- a
    # deactivated item (removed by the user) must not count against the
    # limit forever, otherwise remove+re-add would permanently shrink a
    # FREE user's effective capacity. Not a DB-level constraint (no unique
    # index enforcing count<=N) -- a check-then-insert race is possible
    # under concurrent requests from the same user, accepted as a known,
    # low-impact limitation (see ADR-016 Sonuc Raporu) rather than adding a
    # trigger for a scenario this single-browser-session app doesn't hit.
    subscription = await SubscriptionService(repository=SubscriptionDBRepository(db)).get_current(payload.user_id)
    if subscription["tier"] == SubscriptionTier.FREE.value:
        existing = await _service(db).list_for_user(payload.user_id)
        active_count = sum(1 for item in existing if item["status"] == "ACTIVE")
        if active_count >= settings.FREE_TIER_WATCHLIST_LIMIT:
            raise HTTPException(
                status_code=403,
                detail={
                    "code": "WATCHLIST_LIMIT_REACHED",
                    "limit": settings.FREE_TIER_WATCHLIST_LIMIT,
                    "message": "FREE plan watchlist limit reached -- upgrade to PREMIUM for unlimited watchlist items.",
                },
            )

    return await _service(db).add_item(payload.model_dump())


@router.get("/users/{user_id}/items")
async def list_watchlist_items(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    ensure_owner(current_user, user_id)
    return {"items": await _service(db).list_for_user(user_id)}


@router.get("/items/{item_id}")
async def get_watchlist_item(
    item_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    item = await _service(db).get_item(item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="watchlist_item_not_found")
    ensure_owner(current_user, item["user_id"])
    return item


@router.post("/items/{item_id}/evaluate")
async def evaluate_watchlist_item(
    item_id: str,
    payload: WatchlistEvaluateRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = _service(db)
    item = await service.get_item(item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="watchlist_item_not_found")
    ensure_owner(current_user, item["user_id"])
    item = await service.evaluate_item(item_id, payload.model_dump())
    if item is None:
        raise HTTPException(status_code=404, detail="watchlist_item_not_found")
    return item


@router.post("/items/{item_id}/deactivate")
async def deactivate_watchlist_item(
    item_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = _service(db)
    item = await service.get_item(item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="watchlist_item_not_found")
    ensure_owner(current_user, item["user_id"])
    item = await service.deactivate_item(item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="watchlist_item_not_found")
    return item


@router.post("/clear")
async def clear_watchlist(
    db: AsyncSession = Depends(get_db),
    # AUTH-006 Parça 3 (ADR-005): OPERATOR+ gerektirir.
    current_user=Depends(require_role(UserRole.OPERATOR)),
):
    return await _service(db).clear()
