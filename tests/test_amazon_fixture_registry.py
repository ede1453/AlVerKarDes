from app.domains.connectors.external_connector_registry import ExternalConnectorRegistry


def test_amazon_fixture_mode_loads_fixture(monkeypatch):
    monkeypatch.setenv("EXTERNAL_CONNECTOR_FIXTURE_MODE", "true")
    monkeypatch.setenv("AMAZON_FIXTURE_PATH", "tests/fixtures/amazon_search_m5.json")
    monkeypatch.setenv("MEDIAMARKT_FIXTURE_PATH", "tests/fixtures/mediamarkt_search_m5.json")

    connectors = ExternalConnectorRegistry().build_default_connectors()

    amazon = [item for item in connectors if item.source == "amazon-de"][0]
    mediamarkt = [item for item in connectors if item.source == "mediamarkt-de"][0]

    assert amazon.fixture_json is not None
    assert mediamarkt.fixture_json is not None
