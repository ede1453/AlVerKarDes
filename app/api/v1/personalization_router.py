from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.domains.personalization.personalization_service import PersonalizationService


class UserPreferenceProfileRequest(BaseModel):
    user_id: str
    preferred_marketplaces: list[str] = Field(default_factory=list)
    blocked_marketplaces: list[str] = Field(default_factory=list)
    preferred_brands: list[str] = Field(default_factory=list)
    max_price: str | None = None
    min_discount_percent: int | None = None
    risk_tolerance: str = "MEDIUM"
    metadata: dict = Field(default_factory=dict)


class PersonalizationOfferRequest(BaseModel):
    id: str | None = None
    offer_id: str | None = None
    marketplace: str
    product_name: str
    price: str
    currency: str = "EUR"
    metadata: dict = Field(default_factory=dict)


class PersonalizationScoreRequest(BaseModel):
    user_id: str
    offers: list[PersonalizationOfferRequest] = Field(default_factory=list)


class CachedPersonalizationScoreRequest(PersonalizationScoreRequest):
    ttl_seconds: int = Field(default=300, ge=1, le=86400)


router = APIRouter(prefix="/personalization", tags=["personalization"])

_service = PersonalizationService()


@router.post("/profiles")
async def upsert_profile(payload: UserPreferenceProfileRequest):
    return _service.upsert_profile(payload.model_dump())


@router.get("/profiles/{user_id}")
async def get_profile(user_id: str):
    profile = _service.get_profile(user_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="profile_not_found")
    return profile


@router.post("/score")
async def score_offers(payload: PersonalizationScoreRequest):
    return _service.score(payload.model_dump())


@router.post("/score-cached")
async def score_offers_cached(payload: CachedPersonalizationScoreRequest):
    return _service.score_cached(payload.model_dump())


@router.post("/clear")
async def clear_personalization():
    return _service.clear()
