from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.domains.identity.dependencies import get_current_user, require_role
from app.domains.identity.models import UserRole
from app.domains.llm_provider_selection.provider_selection_service import (
    ProviderSelectionService,
)


class ProviderSelectionRequestBody(BaseModel):
    candidate_providers: list[str] = Field(default_factory=lambda: ["mock", "openai", "local"])
    preferred_provider: str | None = None
    require_available: bool = True
    max_latency_ms: int | None = Field(default=None, ge=0)


router = APIRouter(prefix="/llm-provider-selection", tags=["llm-provider-selection"])


@router.post("/select")
async def select_provider(
    payload: ProviderSelectionRequestBody,
    # AUTH-006 Parça 3 (ADR-005): OPERATOR+ gerektirir.
    current_user=Depends(require_role(UserRole.OPERATOR)),
):
    return ProviderSelectionService().select(payload.model_dump())
