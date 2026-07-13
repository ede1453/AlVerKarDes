from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.domains.recommendations.repository import RecommendationRepository
from app.domains.recommendations.schemas import RecommendationRequest
from app.domains.recommendations.service import RecommendationService

router = APIRouter()


@router.post("/analyze")
async def analyze_product(payload: RecommendationRequest, db: AsyncSession = Depends(get_db)):
    return await RecommendationService(db).analyze(
        product_url=payload.product_url,
        product_name=payload.product_name,
        offer_id=payload.offer_id,
        user_context=payload.user_context,
    )


@router.get("/sessions/{session_id}")
async def get_session_recommendations(session_id: UUID, db: AsyncSession = Depends(get_db)):
    recommendations = await RecommendationRepository(db).list_for_session(session_id)
    return {
        "session_id": str(session_id),
        "recommendations": [
            {
                "id": str(item.id),
                "decision": str(item.decision),
                "confidence": float(item.confidence),
                "summary": item.summary,
                "payload": item.recommendation_payload,
            }
            for item in recommendations
        ],
    }
