from app.domains.marketplace_connectors.connector_base import MarketplaceConnector
from app.domains.marketplace_connectors.external_boundary_connector import (
    ExternalBoundaryMarketplaceConnector,
)
from app.domains.marketplace_connectors.mock_connector import MockMarketplaceConnector


class MarketplaceConnectorRegistry:
    def __init__(self):
        self._connectors: dict[str, MarketplaceConnector] = {}
        self.register(MockMarketplaceConnector())
        for name in ["amazon", "saturn", "mediamarkt", "otto", "idealo", "ebay"]:
            self.register(ExternalBoundaryMarketplaceConnector(name))

    def register(self, connector: MarketplaceConnector):
        self._connectors[connector.name] = connector

    def get(self, name: str):
        return self._connectors.get(name)

    def list(self):
        return [
            {
                "name": name,
                "available": True,
                "external": connector.external,
            }
            for name, connector in sorted(self._connectors.items())
        ]


_default_registry = MarketplaceConnectorRegistry()


def get_marketplace_connector_registry():
    return _default_registry
