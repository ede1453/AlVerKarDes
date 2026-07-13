from app.domains.commerce_ingestion.runtime import ConnectorRuntimeService


def test_rc118_duplicate_execution_is_idempotent():
    service = ConnectorRuntimeService()
    config = {
        "fixture_path": "tests/fixtures/commerce_ingestion/amazon_de_sample.json"
    }
    first = service.execute_connector(
        source_id="amazon-de",
        adapter_type="fixture_json",
        source_config=config,
    )
    second = service.execute_connector(
        source_id="amazon-de",
        adapter_type="fixture_json",
        source_config=config,
    )
    assert first["run"]["ingested_count"] == 2
    assert second["run"]["ingested_count"] == 0
    assert second["run"]["duplicate_count"] == 2
