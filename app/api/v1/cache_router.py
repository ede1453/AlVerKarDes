from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.domains.cache.cache_service import CacheService
from app.domains.identity.dependencies import get_current_user, require_role
from app.domains.identity.models import UserRole


class CacheBuildKeyRequest(BaseModel):
    namespace: str = "default"
    payload: dict = Field(default_factory=dict)


class CacheSetRequest(BaseModel):
    key: str
    value: dict = Field(default_factory=dict)
    ttl_seconds: int = Field(default=300, ge=1, le=86400)


class CacheGetRequest(BaseModel):
    key: str


router = APIRouter(prefix="/cache", tags=["cache"])

_service = CacheService()


@router.get("/status")
async def get_cache_status(
    # AUTH-006 Parça 3 (ADR-005): OPERATOR+ gerektirir.
    current_user=Depends(require_role(UserRole.OPERATOR)),
):
    return _service.status()


@router.post("/key")
async def build_cache_key(
    payload: CacheBuildKeyRequest,
    # AUTH-006 Parça 3 (ADR-005): OPERATOR+ gerektirir.
    current_user=Depends(require_role(UserRole.OPERATOR)),
):
    return _service.build_key(payload.model_dump())


@router.post("/set")
async def set_cache(
    payload: CacheSetRequest,
    # AUTH-006 Parça 3 (ADR-005): OPERATOR+ gerektirir.
    current_user=Depends(require_role(UserRole.OPERATOR)),
):
    return _service.set(payload.model_dump())


@router.post("/get")
async def get_cache(
    payload: CacheGetRequest,
    # AUTH-006 Parça 3 (ADR-005): OPERATOR+ gerektirir.
    current_user=Depends(require_role(UserRole.OPERATOR)),
):
    return _service.get(payload.model_dump())


@router.post("/clear")
async def clear_cache(
    # AUTH-006 Parça 3 (ADR-005): OPERATOR+ gerektirir.
    current_user=Depends(require_role(UserRole.OPERATOR)),
):
    return _service.clear()
