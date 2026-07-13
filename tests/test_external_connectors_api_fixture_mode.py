from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_external_connectors_search_returns_mediamarkt_fixture(monkeypatch):
    monkeypatch.setenv("EXTERNAL_CONNECTOR_FIXTURE_MODE", "true")
    monkeypatch.setenv("MEDIAMARKT_FIXTURE_PATH", "tests/fixtures/mediamarkt_search_m5.json")

    response = client.get("/api/v1/external-connectors/search?query=M5&country=DE")

    assert response.status_code == 200

    data = response.json()

    assert data["query"] == "M5"
    assert data["country"] == "DE"
    assert data["offer_count"] >= 2

    sources = {item["source"] for item in data["offers"]}
    assert "mediamarkt-de" in sources

    assert data["errors"] == []
