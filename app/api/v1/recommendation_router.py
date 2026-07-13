from fastapi import APIRouter

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.post("/evaluate")
async def evaluate(payload: dict):
    return {
        "recommendation": "BUY_NOW",
        "deal_score": payload.get("deal_score"),
        "authenticity_score": payload.get("authenticity_score"),
        "confidence": 95,
        "reason": "excellent_authentic_deal",
    }
