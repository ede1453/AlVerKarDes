from abc import ABC, abstractmethod

from app.domains.marketplace_connectors.connector_models import (
    MarketplaceConnectorQuery,
    MarketplaceConnectorResult,
)


class MarketplaceConnector(ABC):
    name: str
    external: bool = True

    @abstractmethod
    def search(self, query: MarketplaceConnectorQuery) -> MarketplaceConnectorResult:
        raise NotImplementedError
