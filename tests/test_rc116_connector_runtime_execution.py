from app.domains.commerce_ingestion.runtime import ConnectorRuntimeService


def test_rc116_execute_fixture_connector():
    service = ConnectorRuntimeService()
    result = service.execute_connector(
        source_id="amazon-de",
        adapter_type="fixture_json",
        source_config={
            "fixture_path": "tests/fixtures/commerce_ingestion/amazon_de_sample.json"
        },
    )
    assert result["executed"] is True
    assert result["run"]["collected_count"] == 2
    assert result["run"]["ingested_count"] == 2
    assert result["run"]["status"] == "COMPLETED"
