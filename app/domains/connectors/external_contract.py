from dataclasses import dataclass
from decimal import Decimal


@dataclass
class ExternalConnectorOffer:
    source: str
    title: str
    url: str
    price: Decimal
    currency: str
    availability: str = "unknown"
    brand: str | None = None
    gtin: str | None = None
    sku: str | None = None
    confidence: float = 70.0


class ExternalConnector:
    source: str

    async def search(self, query: str, country: str = "DE") -> list[ExternalConnectorOffer]:
        raise NotImplementedError
