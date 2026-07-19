from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.internal_service_auth import require_internal_service_key
from app.domains.connectors.external_connector_bridge import ExternalConnectorBridge
from app.domains.connectors.external_connector_registry import ExternalConnectorRegistry
from app.domains.connectors.external_ingestion_service import ExternalConnectorIngestionService

router = APIRouter(prefix="/external-connectors", tags=["external-connectors"])


@router.get("/sources")
async def list_external_connector_sources():
    registry = ExternalConnectorRegistry()
    return {
        "sources": registry.list_sources(),
        "count": len(registry.list_sources()),
    }


@router.get("/search")
async def search_external_connectors(query: str, country: str = "DE"):
    connectors = ExternalConnectorRegistry().build_default_connectors()
    result = await ExternalConnectorBridge(connectors).search_all(
        query=query,
        country=country,
    )

    return {
        "query": result["query"],
        "country": result["country"],
        "offer_count": len(result["results"]),
        "offers": [
            {
                "source": item.source,
                "title": item.title,
                "url": item.url,
                "price": item.price,
                "currency": item.currency,
                "availability": item.availability,
                "brand": item.brand,
                "gtin": item.gtin,
                "sku": item.sku,
                "confidence": item.confidence,
            }
            for item in result["results"]
        ],
        "errors": result["errors"],
    }


@router.post("/ingest")
async def ingest_external_connectors(
    query: str,
    country: str = "DE",
    db: AsyncSession = Depends(get_db),
    # AUTH-004 (ADR-006): servis-arası çağrı, X-Internal-Service-Key gerektirir.
    internal_service=Depends(require_internal_service_key),
):
    return await ExternalConnectorIngestionService(db).search_and_ingest(
        query=query,
        country=country,
    )
