from app.domains.market.connectors.base import FeedConnector
from app.domains.market.connectors.csv_connector import CSVFeedConnector
from app.domains.market.connectors.json_connector import JSONFeedConnector


class FeedConnectorRegistry:
    def __init__(self):
        self._connectors: dict[str, FeedConnector] = {}

    def register(self, connector: FeedConnector) -> None:
        self._connectors[connector.name] = connector

    def get(self, name: str) -> FeedConnector:
        if name not in self._connectors:
            raise KeyError(f"Unknown connector: {name}")
        return self._connectors[name]


def create_default_feed_registry() -> FeedConnectorRegistry:
    registry = FeedConnectorRegistry()
    registry.register(CSVFeedConnector())
    registry.register(JSONFeedConnector())
    return registry
