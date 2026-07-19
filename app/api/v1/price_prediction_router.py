from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.domains.price_prediction.price_prediction_service import PricePredictionService
from app.domains.identity.dependencies import get_current_user


class PricePredictionRequest(BaseModel):
    product_key: str
    price_history: dict = Field(default_factory=dict)
    prediction_horizon_days: int = Field(default=7, ge=1, le=365)


class CachedPricePredictionRequest(PricePredictionRequest):
    ttl_seconds: int = Field(default=300, ge=1, le=86400)


router = APIRouter(prefix="/price-prediction", tags=["price-prediction"])

_service = PricePredictionService()


@router.post("/predict")
async def predict_price(
    payload: PricePredictionRequest,
    current_user=Depends(get_current_user),
):
    return _service.predict(payload.model_dump())


@router.post("/predict-cached")
async def predict_price_cached(
    payload: CachedPricePredictionRequest,
    current_user=Depends(get_current_user),
):
    return _service.predict_cached(payload.model_dump())
