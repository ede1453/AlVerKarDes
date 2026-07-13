from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.domains.application.search_recommend_service import SearchRecommendService
from app.domains.connectors.ingestion_router import build_demo_manager

router = APIRouter(prefix="/application", tags=["application"])


class SearchRecommendRequest(BaseModel):
    query: str
    country: str = "DE"
    user_context: dict = Field(default_factory=dict)


@router.post("/search-recommend")
async def search_recommend(payload: SearchRecommendRequest, db: AsyncSession = Depends(get_db)):
    service = SearchRecommendService(db=db, manager=build_demo_manager())
    result = await service.run(
        query=payload.query,
        country=payload.country,
        user_context=payload.user_context,
    )

    return {
        "query": result.query,
        "country": result.country,
        "status": result.status,
        "selected_offer_id": result.selected_offer_id,
        "ingestion": result.ingestion,
        "recommendation": result.recommendation,
        "error": result.error,
    }
