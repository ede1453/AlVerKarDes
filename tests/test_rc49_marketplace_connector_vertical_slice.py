from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_marketplace_connector_vertical_slice_to_aggregation():
    connector_response = client.post(
        "/api/v1/marketplace-connectors/search",
        json={
            "query": "MacBook Air",
            "marketplace": "mock_marketplace",
            "connector": "mock_marketplace",
            "limit": 5,
        },
    )
    assert connector_response.status_code == 200
    offers = connector_response.json()["offers"]

    aggregation_response = client.post(
        "/api/v1/marketplace-aggregation/aggregate",
        json={
            "query": "MacBook Air",
            "offers": offers,
        },
    )

    assert aggregation_response.status_code == 200
    assert aggregation_response.json()["offer_count"] == 1
