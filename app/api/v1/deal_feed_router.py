from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.domains.deal_feed.real_source_service import RealDealFeedSourceService
from app.domains.deal_feed.service import (
    DealFeedBuilder,
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
async def query_deal_feed(
    payload: FeedRequest,
    db: AsyncSession = Depends(get_db),
):
    # CLIENT-002d: gercekten ingest edilmis market.Price verisine baglandi
    # -- eskiden burasi sadece _service._deals'a (POST /deal-feed/ingest ile
    # elle beslenen, hicbir gercek connector'a bagli olmayan in-memory bir
    # depo) bakiyordu, hic ingest edilmemis olsa bile hicbir sey uydurmuyordu
    # ama gercek veriye de hic bagli degildi -- kullanici arayuzunde "gercek
    # firsat" olarak sunulamazdi. Skorlama/dedup/kisisellestirme motoru
    # (DealFeedBuilder) DEGISMEDI, hala tests/test_rc205_deal_feed_service.py
    # ile ayni sekilde birim test ediliyor -- sadece girdisi artik gercek.
    # /deal-feed/ingest ve /deal-feed/deals/{deal_id} bu turda dokunulmadi,
    # hala eski in-memory _service uzerinden calisiyor (bilinen, kayitli bir
    # tutarsizlik -- bkz. WIKI_ROOT).
    real_deals = await RealDealFeedSourceService(db).list_real_deals()
    return DealFeedBuilder().build(
        deals=real_deals,
        preferences=payload.preferences,
        minimum_confidence=payload.minimum_confidence,
        limit=payload.limit,
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
