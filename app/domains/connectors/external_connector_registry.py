import os
from pathlib import Path

from app.domains.connectors.adapters.amazon_de import AmazonDEConnector
from app.domains.connectors.adapters.mediamarkt_de import MediaMarktDEConnector
from app.domains.connectors.adapters.saturn_de import SaturnDEConnector


class ExternalConnectorRegistry:
    def build_default_connectors(self):
        return [
            self._build_amazon_connector(),
            self._build_mediamarkt_connector(),
            SaturnDEConnector(),
        ]

    def list_sources(self) -> list[str]:
        return [connector.source for connector in self.build_default_connectors()]

    def _fixture_enabled(self) -> bool:
        return os.getenv("EXTERNAL_CONNECTOR_FIXTURE_MODE", "").lower() in {"1", "true", "yes"}

    def _build_amazon_connector(self):
        if not self._fixture_enabled():
            return AmazonDEConnector()

        fixture_path = Path(
            os.getenv(
                "AMAZON_FIXTURE_PATH",
                "tests/fixtures/amazon_search_m5.json",
            )
        )

        if not fixture_path.exists():
            return AmazonDEConnector()

        return AmazonDEConnector(
            fixture_json=fixture_path.read_text(encoding="utf-8")
        )

    def _build_mediamarkt_connector(self):
        if not self._fixture_enabled():
            return MediaMarktDEConnector()

        fixture_path = Path(
            os.getenv(
                "MEDIAMARKT_FIXTURE_PATH",
                "tests/fixtures/mediamarkt_search_m5.json",
            )
        )

        if not fixture_path.exists():
            return MediaMarktDEConnector()

        return MediaMarktDEConnector(
            fixture_json=fixture_path.read_text(encoding="utf-8")
        )
