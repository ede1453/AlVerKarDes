from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.domains.crawler.crawler_service import CrawlerService


class CrawlRequestModel(BaseModel):
    url: str
    connector: str = "mock"
    obey_robots_txt: bool = True
    allow_external_fetch: bool = False
    timeout_ms: int = Field(default=3000, ge=100, le=30000)
    metadata: dict = Field(default_factory=dict)


router = APIRouter(prefix="/crawler", tags=["crawler"])

_service = CrawlerService()


@router.post("/crawl")
async def crawl_url(payload: CrawlRequestModel):
    return _service.crawl(payload.model_dump())
