from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_marketplace_connectors_list_api():
    response = client.get("/api/v1/marketplace-connectors")

    assert response.status_code == 200
    names = [item["name"] for item in response.json()["connectors"]]
    assert "mock_marketplace" in names
    assert "amazon" in names


def test_marketplace_connector_search_api_mock():
    response = client.post(
        "/api/v1/marketplace-connectors/search",
        json={
            "query": "MacBook Air",
            "marketplace": "mock_marketplace",
            "connector": "mock_marketplace",
            "limit": 5,
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "COMPLETED"
    assert response.json()["offer_count"] == 5
    assert len(response.json()["offers"]) == 5


def test_marketplace_connector_search_api_external_boundary():
    response = client.post(
        "/api/v1/marketplace-connectors/search",
        json={
            "query": "MacBook Air",
            "marketplace": "amazon",
            "connector": "amazon",
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "CONNECTOR_NOT_CONFIGURED"
