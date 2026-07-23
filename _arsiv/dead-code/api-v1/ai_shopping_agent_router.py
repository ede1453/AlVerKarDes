from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.domains.ai_shopping_agent.agent_service import AIShoppingAgentService
from app.domains.identity.dependencies import get_current_user


class AgentOfferRequest(BaseModel):
    id: str | None = None
    marketplace: str
    seller: str | None = None
    product_name: str
    price: str
    currency: str = "EUR"
    metadata: dict = Field(default_factory=dict)


class AgentProfileRequest(BaseModel):
    preferred_marketplaces: list[str] = Field(default_factory=list)
    blocked_marketplaces: list[str] = Field(default_factory=list)
    preferred_brands: list[str] = Field(default_factory=list)
    max_price: str | None = None
    min_discount_percent: int | None = None
    risk_tolerance: str = "MEDIUM"
    metadata: dict = Field(default_factory=dict)


class AgentRunRequest(BaseModel):
    query: str
    user_id: str | None = None
    marketplaces: list[str] = Field(default_factory=list)
    offers: list[AgentOfferRequest] = Field(default_factory=list)
    profile: AgentProfileRequest | None = None


class CachedAgentRunRequest(AgentRunRequest):
    ttl_seconds: int = Field(default=300, ge=1, le=86400)


router = APIRouter(prefix="/ai-shopping-agent", tags=["ai-shopping-agent"])

_service = AIShoppingAgentService()


@router.post("/run")
async def run_ai_shopping_agent(
    payload: AgentRunRequest,
    current_user=Depends(get_current_user),
):
    return _service.run(payload.model_dump())


@router.post("/run-cached")
async def run_ai_shopping_agent_cached(
    payload: CachedAgentRunRequest,
    current_user=Depends(get_current_user),
):
    return _service.run_cached(payload.model_dump())
