from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.domains.identity.dependencies import get_current_user, require_role
from app.domains.identity.models import UserRole
from app.domains.rate_limits.rate_limit_service import RateLimitService


class RateLimitCheckRequest(BaseModel):
    key: str = "anonymous"
    scope: str = "llm_gateway"


router = APIRouter(prefix="/rate-limits", tags=["rate-limits"])

_service = RateLimitService()


@router.post("/check")
async def check_rate_limit(
    payload: RateLimitCheckRequest,
    # AUTH-006 Parça 3 (ADR-005): OPERATOR+ gerektirir.
    current_user=Depends(require_role(UserRole.OPERATOR)),
):
    return _service.check(payload.model_dump())
