import json
from pathlib import Path

from app.domains.market.connectors.base import FeedConnector
from app.domains.market.connectors.schemas import FeedItem


class JSONFeedConnector(FeedConnector):
    name = "json_feed"

    def parse(self, path: Path) -> list[FeedItem]:
        data = json.loads(path.read_text(encoding="utf-8"))
        rows = data.get("items", []) if isinstance(data, dict) else data
        return [FeedItem(**row) for row in rows]
