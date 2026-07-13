from app.domains.commerce_ingestion.operations import ConnectorOperationsService


def test_rc124_aggregate_metrics():
    service = ConnectorOperationsService()
    service.record_run_metrics(
        source_id="amazon-de",
        collected_count=10,
        ingested_count=8,
        failed_count=2,
        duration_ms=1000,
    )
    service.record_run_metrics(
        source_id="amazon-de",
        collected_count=5,
        ingested_count=5,
        failed_count=0,
        duration_ms=500,
    )
    metrics = service.get_metrics("amazon-de")
    assert metrics["run_count"] == 2
    assert metrics["total_ingested"] == 13
    assert metrics["total_failed"] == 2
    assert metrics["average_duration_ms"] == 750.0
