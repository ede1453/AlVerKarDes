from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.internal_service_auth import require_internal_service_key
from app.domains.connectors.ingestion_service import ConnectorIngestionService
from app.domains.connectors.manager import ConnectorManager
from app.domains.connectors.marketplace_adapters import build_live_connectors

router = APIRouter(prefix="/connectors", tags=["connectors-ingestion"])


def build_live_manager() -> ConnectorManager:
    # PARÇA B (bkz. ADR-007): Amazon/eBay/Idealo'nun TEK paylaşılan
    # ingestion yolu -- her connector kendi özel bir DB yazma yolu
    # açmıyor, hepsi aynı ConnectorManager/ConnectorIngestionService
    # zincirinden market.Price'a yazıyor.
    return ConnectorManager(build_live_connectors())


@router.post("/ingest")
async def ingest_connector_results(
    query: str,
    country: str = "DE",
    db: AsyncSession = Depends(get_db),
    # AUTH-004 (ADR-006): servis-arası çağrı, X-Internal-Service-Key gerektirir.
    internal_service=Depends(require_internal_service_key),
):
    service = ConnectorIngestionService(db=db, manager=build_live_manager())
    result = await service.search_and_ingest(query=query, country=country)
    return {
        "query": result.query,
        "country": result.country,
        "total_offers": result.total_offers,
        "ingested_count": result.ingested_count,
        "skipped_count": result.skipped_count,
        "items": [item.__dict__ for item in result.items],
        "connector_errors": result.connector_errors,
    }
