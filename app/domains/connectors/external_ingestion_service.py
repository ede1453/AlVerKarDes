from app.domains.connectors.external_connector_bridge import ExternalConnectorBridge
from app.domains.connectors.external_connector_registry import ExternalConnectorRegistry
from app.domains.connectors.ingestion_service import ConnectorIngestionService
from app.domains.connectors.manager import ConnectorManager


class ExternalManualConnector:
    def __init__(self, results):
        self.results = results

    async def search(self, query: str, country: str = "DE"):
        return self.results


class ExternalConnectorIngestionService:
    def __init__(self, db):
        self.db = db

    async def search_and_ingest(self, query: str, country: str = "DE"):
        connectors = ExternalConnectorRegistry().build_default_connectors()
        bridge_result = await ExternalConnectorBridge(connectors).search_all(
            query=query,
            country=country,
        )

        manager = ConnectorManager([
            ExternalManualConnector(bridge_result["results"])
        ])

        ingestion = await ConnectorIngestionService(
            db=self.db,
            manager=manager,
        ).search_and_ingest(
            query=query,
            country=country,
        )

        return {
            "query": query,
            "country": country,
            "external_offer_count": len(bridge_result["results"]),
            "external_errors": bridge_result["errors"],
            "ingestion": {
                "query": ingestion.query,
                "country": ingestion.country,
                "total_offers": ingestion.total_offers,
                "ingested_count": ingestion.ingested_count,
                "skipped_count": ingestion.skipped_count,
                "items": [item.__dict__ for item in ingestion.items],
                "connector_errors": ingestion.connector_errors,
            },
        }