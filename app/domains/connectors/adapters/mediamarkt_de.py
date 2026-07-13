from app.domains.connectors.external_contract import ExternalConnectorOffer
from app.domains.connectors.http_connector_base import HttpConnectorBase
from app.domains.connectors.parsers.mediamarkt_parser import MediaMarktProductParser


class MediaMarktDEConnector(HttpConnectorBase):
    source = "mediamarkt-de"

    def __init__(self, *, timeout_seconds: float = 10.0, fixture_json: str | None = None):
        super().__init__(timeout_seconds=timeout_seconds)
        self.fixture_json = fixture_json
        self.parser = MediaMarktProductParser()

    async def search(self, query: str, country: str = "DE") -> list[ExternalConnectorOffer]:
        if self.fixture_json:
            return [
                offer for offer in self.parser.parse_json_items(self.fixture_json)
                if query.lower() in offer.title.lower()
            ]

        # RC3: live HTTP integration intentionally disabled until provider rules/API are confirmed.
        return []
