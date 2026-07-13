from app.domains.events.event_repository_factory import reset_event_repository
from app.domains.marketplace_connectors.connector_service import MarketplaceConnectorService


def test_connector_service_mock_search_emits_event():
    reset_event_repository()
    service = MarketplaceConnectorService()

    result = service.search(
        {
            "query": "MacBook Air",
            "marketplace": "mock_marketplace",
            "connector": "mock_marketplace",
            "limit": 5,
        }
    )

    assert result["status"] == "COMPLETED"
    assert result["offer_count"] == 1

    events = service.event_bus_service.list_recent(
        {"event_type": "marketplace_connector.search_completed", "source": "marketplace_connectors"}
    )
    assert events


def test_connector_service_external_boundary_is_safe_disabled():
    service = MarketplaceConnectorService()

    result = service.search(
        {
            "query": "MacBook Air",
            "marketplace": "amazon",
            "connector": "amazon",
        }
    )

    assert result["status"] == "CONNECTOR_NOT_CONFIGURED"
    assert result["offer_count"] == 0
