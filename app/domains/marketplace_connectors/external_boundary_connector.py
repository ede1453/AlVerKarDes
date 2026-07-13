from app.domains.marketplace_connectors.connector_base import MarketplaceConnector
from app.domains.marketplace_connectors.connector_models import (
    MarketplaceConnectorQuery,
    MarketplaceConnectorResult,
)


class ExternalBoundaryMarketplaceConnector(MarketplaceConnector):
    external = True

    def __init__(self, name: str):
        self.name = name

    def search(self, query: MarketplaceConnectorQuery) -> MarketplaceConnectorResult:
        return MarketplaceConnectorResult(
            marketplace=query.marketplace,
            query=query.query,
            status="CONNECTOR_NOT_CONFIGURED",
            offer_count=0,
            offers=[],
            metadata={
                "connector": self.name,
                "external": True,
                "message": "External marketplace connector is intentionally disabled until explicitly configured.",
            },
        )
