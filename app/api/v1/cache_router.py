from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.domains.cache.cache_service import CacheService


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
async def get_cache_status():
    return _service.status()


@router.post("/key")
async def build_cache_key(payload: CacheBuildKeyRequest):
    return _service.build_key(payload.model_dump())


@router.post("/set")
async def set_cache(payload: CacheSetRequest):
    return _service.set(payload.model_dump())


@router.post("/get")
async def get_cache(payload: CacheGetRequest):
    return _service.get(payload.model_dump())


@router.post("/clear")
async def clear_cache():
    return _service.clear()
