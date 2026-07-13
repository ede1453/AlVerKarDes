from abc import ABC, abstractmethod
from pathlib import Path

from app.domains.market.connectors.schemas import FeedItem


class FeedConnector(ABC):
    name: str

    @abstractmethod
    def parse(self, path: Path) -> list[FeedItem]:
        raise NotImplementedError
