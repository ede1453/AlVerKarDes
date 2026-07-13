from app.domains.commerce_ingestion.operations import ConnectorOperationsService


def test_rc122_exponential_retry():
    service = ConnectorOperationsService()
    first = service.calculate_retry(
        operation_key="amazon-run",
        max_attempts=3,
        base_delay_seconds=10,
        multiplier=2,
    )
    second = service.calculate_retry(
        operation_key="amazon-run",
        max_attempts=3,
        base_delay_seconds=10,
        multiplier=2,
    )
    assert first["delay_seconds"] == 10
    assert second["delay_seconds"] == 20
    assert second["attempt"] == 2

def test_rc122_retry_reset():
    service = ConnectorOperationsService()
    service.calculate_retry(operation_key="run")
    service.reset_retry("run")
    result = service.calculate_retry(operation_key="run")
    assert result["attempt"] == 1
