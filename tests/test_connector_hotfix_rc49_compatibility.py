from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_rc49_list_contract_is_preserved():
    response = client.get(
        "/api/v1/marketplace-connectors"
    )

    assert response.status_code == 200
    data = response.json()

    assert data["count"] >= 7
    assert any(
        connector["name"] == "mock_marketplace"
        for connector in data["connectors"]
    )


def test_rc49_mock_search_contract_is_preserved():
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
    data = response.json()

    assert data["executed"] is True
    assert data["offer_count"] == 5
    assert len(data["offers"]) == 5


def test_rc49_external_boundary_is_preserved():
    response = client.post(
        "/api/v1/marketplace-connectors/search",
        json={
            "query": "MacBook Air",
            "marketplace": "amazon",
            "connector": "amazon",
            "limit": 5,
        },
    )

    assert response.status_code == 200
    data = response.json()

    assert data["executed"] is False
    assert data["external"] is True
    assert data["offer_count"] == 0
