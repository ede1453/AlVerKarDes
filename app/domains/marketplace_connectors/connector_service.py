from app.domains.events.event_bus_service import EventBusService
from app.domains.marketplace_connectors.connector_models import MarketplaceConnectorQuery
from app.domains.marketplace_connectors.connector_registry import (
    get_marketplace_connector_registry,
)
from app.domains.marketplace_connectors.connector_serializer import serialize_result


class MarketplaceConnectorService:
    def __init__(self, registry=None, event_bus_service: EventBusService | None = None):
        self.registry = registry or get_marketplace_connector_registry()
        self.event_bus_service = event_bus_service or EventBusService()

    def list_connectors(self):
        return {"connectors": self.registry.list()}

    def search(self, payload: dict):
        connector_name = payload.get("connector") or payload["marketplace"]
        connector = self.registry.get(connector_name)
        if connector is None:
            return {
                "marketplace": payload["marketplace"],
                "query": payload["query"],
                "status": "CONNECTOR_NOT_FOUND",
                "offer_count": 0,
                "offers": [],
                "metadata": {"connector": connector_name},
            }

        result = connector.search(
            MarketplaceConnectorQuery(
                query=payload["query"],
                marketplace=payload["marketplace"],
                limit=payload.get("limit", 10),
                locale=payload.get("locale", "de-DE"),
                currency=payload.get("currency", "EUR"),
                metadata=payload.get("metadata", {}),
            )
        )
        serialized = serialize_result(result)

        self.event_bus_service.publish(
            {
                "event_type": "marketplace_connector.search_completed",
                "source": "marketplace_connectors",
                "payload": {
                    "connector": connector_name,
                    "marketplace": serialized["marketplace"],
                    "query": serialized["query"],
                    "status": serialized["status"],
                    "offer_count": serialized["offer_count"],
                },
                "metadata": {"event_version": "event_v1"},
            }
        )

        return serialized
