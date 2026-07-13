from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.domains.llm_provider_health.provider_health_service import (
    ProviderHealthService,
)


class ProviderHealthCheckRequestBody(BaseModel):
    providers: list[str] = Field(default_factory=lambda: ["mock", "openai", "local"])
    include_external_boundaries: bool = True


router = APIRouter(prefix="/llm-provider-health", tags=["llm-provider-health"])


@router.post("/check")
async def check_provider_health(payload: ProviderHealthCheckRequestBody):
    return ProviderHealthService().check(payload.model_dump())


@router.get("/summary")
async def get_provider_health_summary():
    return ProviderHealthService().check(
        {
            "providers": ["mock", "openai", "local"],
            "include_external_boundaries": True,
        }
    )
