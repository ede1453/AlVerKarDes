from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.domains.identity.dependencies import get_current_user, require_role
from app.domains.identity.models import UserRole
from app.domains.llm_streaming.streaming_service import LLMStreamingService


class LLMStreamingPreviewRequest(BaseModel):
    text: str
    event_type: str = "token"
    chunk_size: int = Field(default=24, ge=1, le=500)
    metadata: dict = Field(default_factory=dict)


router = APIRouter(prefix="/llm-streaming", tags=["llm-streaming"])


@router.post("/preview")
async def preview_stream(
    payload: LLMStreamingPreviewRequest,
    # AUTH-006 Parça 3 (ADR-005): OPERATOR+ gerektirir.
    current_user=Depends(require_role(UserRole.OPERATOR)),
):
    return LLMStreamingService().preview(payload.model_dump())


@router.post("/sse")
async def stream_sse(
    payload: LLMStreamingPreviewRequest,
    # AUTH-006 Parça 3 (ADR-005): OPERATOR+ gerektirir.
    current_user=Depends(require_role(UserRole.OPERATOR)),
):
    return StreamingResponse(
        LLMStreamingService().sse_lines(payload.model_dump()),
        media_type="text/event-stream",
    )
