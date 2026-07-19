from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.domains.identity.dependencies import get_current_user, require_role
from app.domains.identity.models import UserRole
from app.domains.llm_provider_gateway.llm_provider_gateway_service import (
    LLMProviderGatewayService,
)
from app.domains.llm_provider_gateway.provider_registry import LLMProviderRegistry


class LLMGatewayGenerateRequest(BaseModel):
    provider: str = "mock"
    model: str = "mock-shopping-explainer"
    system_prompt: str = ""
    user_prompt: str = ""
    guardrails: list[str] = Field(default_factory=list)
    structured_context: dict = Field(default_factory=dict)
    max_tokens: int = Field(default=500, ge=1, le=4000)
    temperature: float = Field(default=0.2, ge=0, le=2)
    prompt_version: str = "shopping_v1"


router = APIRouter(prefix="/llm-gateway", tags=["llm-gateway"])


@router.post("/generate")
async def generate_with_llm_gateway(
    payload: LLMGatewayGenerateRequest,
    # AUTH-006 Parça 3 (ADR-005): OPERATOR+ gerektirir.
    current_user=Depends(require_role(UserRole.OPERATOR)),
):
    return LLMProviderGatewayService().generate(payload.model_dump())


@router.get("/providers")
async def list_llm_gateway_providers(
    # AUTH-006 Parça 3 (ADR-005): OPERATOR+ gerektirir.
    current_user=Depends(require_role(UserRole.OPERATOR)),
):
    return {
        "providers": LLMProviderRegistry().describe(),
        "default_provider": "mock",
    }
