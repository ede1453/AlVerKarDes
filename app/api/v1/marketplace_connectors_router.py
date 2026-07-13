from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.domains.marketplace_connectors.connector_service import MarketplaceConnectorService


class MarketplaceConnectorSearchRequest(BaseModel):
    query: str
    marketplace: str
    connector: str | None = None
    limit: int = Field(default=10, ge=1, le=100)
    locale: str = "de-DE"
    currency: str = "EUR"
    metadata: dict = Field(default_factory=dict)


router = APIRouter(prefix="/marketplace-connectors", tags=["marketplace-connectors"])

_service = MarketplaceConnectorService()


@router.get("")
async def list_marketplace_connectors():
    return _service.list_connectors()


@router.post("/search")
async def search_marketplace_connector(payload: MarketplaceConnectorSearchRequest):
    return _service.search(payload.model_dump())
