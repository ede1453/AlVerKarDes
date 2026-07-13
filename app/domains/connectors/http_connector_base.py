import httpx

from app.domains.connectors.external_contract import ExternalConnector, ExternalConnectorOffer


class HttpConnectorBase(ExternalConnector):
    source = "http-base"

    def __init__(self, *, timeout_seconds: float = 10.0):
        self.timeout_seconds = timeout_seconds

    async def get_html(self, url: str) -> str:
        async with httpx.AsyncClient(timeout=self.timeout_seconds, follow_redirects=True) as client:
            response = await client.get(
                url,
                headers={
                    "User-Agent": "Mozilla/5.0 AI-Consumer-Intelligence/RC3",
                    "Accept-Language": "de-DE,de;q=0.9,en;q=0.8",
                },
            )
            response.raise_for_status()
            return response.text

    async def search(self, query: str, country: str = "DE") -> list[ExternalConnectorOffer]:
        raise NotImplementedError
