from fastapi import APIRouter
from pydantic import BaseModel, Field

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
async def select_provider(payload: ProviderSelectionRequestBody):
    return ProviderSelectionService().select(payload.model_dump())
