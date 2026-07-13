from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

def test_rc120_rc124_routes_registered():
    paths = client.get("/openapi.json").json()["paths"]
    for path in [
        "/api/v1/connector-operations/clear",
        "/api/v1/connector-operations/credential-profiles",
        "/api/v1/connector-operations/credential-profiles/{profile_id}",
        "/api/v1/connector-operations/validate-items",
        "/api/v1/connector-operations/retry",
        "/api/v1/connector-operations/retry/{operation_key}/reset",
        "/api/v1/connector-operations/schedules",
        "/api/v1/connector-operations/schedules/{schedule_id}/mark-run",
        "/api/v1/connector-operations/schedules/due",
        "/api/v1/connector-operations/metrics",
        "/api/v1/connector-operations/metrics/{source_id}",
    ]:
        assert path in paths
