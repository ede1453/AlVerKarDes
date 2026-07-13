from fastapi import APIRouter
from pydantic import BaseModel

from app.domains.rate_limits.rate_limit_service import RateLimitService


class RateLimitCheckRequest(BaseModel):
    key: str = "anonymous"
    scope: str = "llm_gateway"


router = APIRouter(prefix="/rate-limits", tags=["rate-limits"])

_service = RateLimitService()


@router.post("/check")
async def check_rate_limit(payload: RateLimitCheckRequest):
    return _service.check(payload.model_dump())
