from pathlib import Path

from app.domains.market.connectors.csv_connector import CSVFeedConnector
from app.domains.market.connectors.json_connector import JSONFeedConnector


def test_csv_connector_parses_sample():
    path = Path("examples/sample_feed.csv")
    if path.exists():
        items = CSVFeedConnector().parse(path)
        assert len(items) >= 1
        assert items[0].price > 0


def test_json_connector_parses_sample():
    path = Path("examples/sample_feed.json")
    if path.exists():
        items = JSONFeedConnector().parse(path)
        assert len(items) >= 1
        assert items[0].store_slug
