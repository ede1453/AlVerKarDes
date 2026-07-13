from app.domains.connectors.external_contract import ExternalConnectorOffer
from app.domains.connectors.http_connector_base import HttpConnectorBase


class SaturnDEConnector(HttpConnectorBase):
    source = "saturn-de"

    async def search(self, query: str, country: str = "DE") -> list[ExternalConnectorOffer]:
        # RC3 placeholder.
        # Real implementation should use official feeds/API where available.
        return []
