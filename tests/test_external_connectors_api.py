from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_external_connectors_sources_endpoint():
    response = client.get("/api/v1/external-connectors/sources")

    assert response.status_code == 200

    data = response.json()

    assert data["count"] >= 3
    assert "amazon-de" in data["sources"]
    assert "mediamarkt-de" in data["sources"]
    assert "saturn-de" in data["sources"]


def test_external_connectors_search_endpoint_placeholder(monkeypatch):
    monkeypatch.delenv("EXTERNAL_CONNECTOR_FIXTURE_MODE", raising=False)
    monkeypatch.delenv("MEDIAMARKT_FIXTURE_PATH", raising=False)
    
    response = client.get("/api/v1/external-connectors/search?query=M5&country=DE")

    assert response.status_code == 200

    data = response.json()

    assert data["query"] == "M5"
    assert data["country"] == "DE"
    assert data["offer_count"] == 0
    assert data["offers"] == []
    assert data["errors"] == []


def test_external_connectors_routes_exist_in_openapi():
    response = client.get("/openapi.json")

    assert response.status_code == 200

    paths = response.json()["paths"]

    assert "/api/v1/external-connectors/sources" in paths
    assert "/api/v1/external-connectors/search" in paths
