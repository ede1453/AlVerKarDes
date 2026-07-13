from app.domains.marketplace_connectors.connector_base import MarketplaceConnector
from app.domains.marketplace_connectors.connector_models import (
    MarketplaceConnectorOffer,
    MarketplaceConnectorQuery,
    MarketplaceConnectorResult,
    create_offer_id,
)


class MockMarketplaceConnector(MarketplaceConnector):
    name = "mock_marketplace"
    external = False

    def search(self, query: MarketplaceConnectorQuery) -> MarketplaceConnectorResult:
        offers = [
            MarketplaceConnectorOffer(
                id=create_offer_id(),
                marketplace=query.marketplace,
                seller="Mock Seller",
                product_name=f"{query.query} Mock Offer",
                price="949.00",
                currency=query.currency,
                availability="IN_STOCK",
                metadata={"connector": self.name, "deterministic": True},
            )
        ][: query.limit]

        return MarketplaceConnectorResult(
            marketplace=query.marketplace,
            query=query.query,
            status="COMPLETED",
            offer_count=len(offers),
            offers=offers,
            metadata={"connector": self.name, "external": self.external},
        )
