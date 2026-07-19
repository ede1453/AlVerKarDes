from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.domains.application.grouped_search_recommend_service import GroupedSearchRecommendService
from app.domains.connectors.ingestion_router import build_live_manager

router = APIRouter(prefix="/application", tags=["application"])


class GroupedSearchRecommendRequest(BaseModel):
    query: str
    country: str = "DE"
    user_context: dict = Field(default_factory=dict)


@router.post("/grouped-search-recommend")
async def grouped_search_recommend(payload: GroupedSearchRecommendRequest, db: AsyncSession = Depends(get_db)):
    result = await GroupedSearchRecommendService(db=db, manager=build_live_manager()).run(
        query=payload.query,
        country=payload.country,
        user_context=payload.user_context,
    )
    return {
        "query": result.query,
        "country": result.country,
        "status": result.status,
        "selected_group_id": result.selected_group_id,
        "selected_offer_id": result.selected_offer_id,
        "consumer_decision": result.consumer_decision,
        "search": result.search,
        "ingestion": result.ingestion,
        "recommendation": result.recommendation,
        "error": result.error,
    }
