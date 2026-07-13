from app.domains.commerce_ingestion.runtime import ConnectorRuntimeService


def test_rc119_connector_events():
    service = ConnectorRuntimeService()
    result = service.execute_connector(
        source_id="amazon-de",
        adapter_type="fixture_json",
        source_config={
            "fixture_path": "tests/fixtures/commerce_ingestion/amazon_de_sample.json"
        },
    )
    events = service.list_events(run_id=result["run"]["run_id"])
    assert events["event_count"] == 2
    assert events["events"][0]["event_type"] == "CONNECTOR_RUNTIME_STARTED"
    assert events["events"][1]["event_type"] == "CONNECTOR_RUNTIME_COMPLETED"
