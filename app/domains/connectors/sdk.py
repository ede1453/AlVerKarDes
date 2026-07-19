from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class ConnectorProductResult:
    source: str
    title: str
    url: str | None = None
    price: float | None = None
    currency: str = "EUR"
    availability: str | None = None
    brand: str | None = None
    gtin: str | None = None
    sku: str | None = None
    raw: dict[str, Any] | None = None
    confidence: float = 0.0
    is_real_data: bool = True


class StoreConnector(ABC):
    source_name: str

    @abstractmethod
    async def search(self, query: str, country: str = "DE") -> list[ConnectorProductResult]:
        raise NotImplementedError

    @abstractmethod
    async def get_product(self, url: str) -> ConnectorProductResult:
        raise NotImplementedError
