from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_rc100_rc104_observability_routes_are_registered():
    paths = client.get("/openapi.json").json()["paths"]

    assert "/api/v1/observability/traces/{trace_id}" in paths
    assert "/api/v1/observability/logs" in paths
    assert "/api/v1/observability/timelines/{correlation_id}" in paths
    assert "/api/v1/observability/audit-events" in paths
    assert "/api/v1/observability/clear" in paths
