from fastapi import APIRouter

from app.domains.connectors.manager import ConnectorManager
from app.domains.connectors.manual_connector import ManualConnector
from app.domains.connectors.sdk import ConnectorProductResult
from app.domains.connectors.search_presenter import ConnectorSearchPresenter

router = APIRouter(prefix="/connectors", tags=["connectors"])


@router.get("/search")
async def search_connectors(query: str, country: str = "DE"):
    manager = ConnectorManager([
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
                title="Apple MBA M5 16/512",
                url="https://example.com/mediamarkt/mba-m5-16-512",
                price=879,
                currency="EUR",
                availability="in_stock",
                confidence=90,
            ),
            ConnectorProductResult(
                source="mock-saturn-de",
                title="MacBook Air M5 (16 GB RAM, 512 GB SSD)",
                url="https://example.com/saturn/macbook-air-m5-16gb-512gb",
                price=869,
                currency="EUR",
                availability="in_stock",
                confidence=92,
            ),
        ])
    ])

    result = await manager.search_all(query=query, country=country)
    return ConnectorSearchPresenter().present(
        query=result.query,
        country=result.country,
        offers=result.offers,
        errors=result.errors,
    )
