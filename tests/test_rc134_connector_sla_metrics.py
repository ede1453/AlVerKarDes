from app.domains.commerce_ingestion.http_execution import (
    ConnectorSlaMetrics,
)


def test_rc134_sla_metrics():
    metrics = ConnectorSlaMetrics()
    metrics.record(
        connector_id="amazon",
        success=True,
        duration_ms=100,
    )
    metrics.record(
        connector_id="amazon",
        success=False,
        duration_ms=300,
    )
    result = metrics.get("amazon")
    assert result["request_count"] == 2
    assert result["success_rate"] == 0.5
    assert result["average_duration_ms"] == 200.0
