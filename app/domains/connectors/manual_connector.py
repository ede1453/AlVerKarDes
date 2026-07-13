from app.domains.connectors.sdk import ConnectorProductResult, StoreConnector


class ManualConnector(StoreConnector):
    source_name = "manual"

    def __init__(self, items: list[ConnectorProductResult] | None = None):
        self.items = items or []

    async def search(self, query: str, country: str = "DE") -> list[ConnectorProductResult]:
        query_l = query.lower()
        return [item for item in self.items if query_l in item.title.lower()]

    async def get_product(self, url: str) -> ConnectorProductResult:
        for item in self.items:
            if item.url == url:
                return item
        raise ValueError(f"Product not found for url: {url}")
