from app.domains.commerce_ingestion.runtime import ConnectorRuntimeService


def test_rc117_price_history_bridge():
    service = ConnectorRuntimeService()
    service.execute_connector(
        source_id="amazon-de",
        adapter_type="fixture_json",
        source_config={
            "fixture_path": "tests/fixtures/commerce_ingestion/amazon_de_sample.json"
        },
    )
    history = service.price_bridge.get_history(
        "apple::macbook-air::m5::16gb::512gb"
    )
    assert history["price_point_count"] == 2
    assert history["latest_price"] == 999.0
    assert history["lowest_price"] == 999.0
    assert history["highest_price"] == 1099.0
