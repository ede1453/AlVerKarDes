from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.domains.smart_alerts.smart_alert_service import SmartAlertService


class SmartAlertEvaluateRequest(BaseModel):
    user_id: str | None = None
    product_key: str
    deal_detection: dict | None = None
    price_prediction: dict | None = None
    personalization: dict | None = None
    channels: list[str] = Field(default_factory=lambda: ["in_app"])


class CachedSmartAlertEvaluateRequest(SmartAlertEvaluateRequest):
    ttl_seconds: int = Field(default=300, ge=1, le=86400)


router = APIRouter(prefix="/smart-alerts", tags=["smart-alerts"])

_service = SmartAlertService()


@router.post("/evaluate")
async def evaluate_smart_alert(payload: SmartAlertEvaluateRequest):
    return _service.evaluate(payload.model_dump())


@router.post("/evaluate-cached")
async def evaluate_smart_alert_cached(payload: CachedSmartAlertEvaluateRequest):
    return _service.evaluate_cached(payload.model_dump())
