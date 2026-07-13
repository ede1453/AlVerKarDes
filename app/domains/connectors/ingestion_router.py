from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.domains.connectors.ingestion_service import ConnectorIngestionService
from app.domains.connectors.manager import ConnectorManager
from app.domains.connectors.manual_connector import ManualConnector
from app.domains.connectors.sdk import ConnectorProductResult

router = APIRouter(prefix="/connectors", tags=["connectors-ingestion"])


def build_demo_manager() -> ConnectorManager:
    return ConnectorManager([
        ManualConnector([
            ConnectorProductResult(
                source="mock-amazon-de",
                title="Apple MacBook Air M5 16GB 512GB",
                url="https://example.com/amazon/macbook-air-m5-16-512",
                price=849,
                currency="EUR",
                availability="in_stock",
                confidence=95,
            ),
            ConnectorProductResult(
                source="mock-mediamarkt-de",
                title="Apple MBA M5 16 GB 512 GB",
                url="https://example.com/mediamarkt/mba-m5-16-512",
                price=879,
                currency="EUR",
                availability="in_stock",
                confidence=90,
            ),
        ])
    ])


@router.post("/ingest")
async def ingest_connector_results(query: str, country: str = "DE", db: AsyncSession = Depends(get_db)):
    service = ConnectorIngestionService(db=db, manager=build_demo_manager())
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
