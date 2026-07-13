from app.domains.connectors.external_connector_registry import ExternalConnectorRegistry


def test_external_connector_registry_fixture_mode(monkeypatch):
    monkeypatch.setenv("EXTERNAL_CONNECTOR_FIXTURE_MODE", "true")
    monkeypatch.setenv("MEDIAMARKT_FIXTURE_PATH", "tests/fixtures/mediamarkt_search_m5.json")

    connectors = ExternalConnectorRegistry().build_default_connectors()

    mediamarkt = [item for item in connectors if item.source == "mediamarkt-de"][0]

    assert mediamarkt.fixture_json is not None
