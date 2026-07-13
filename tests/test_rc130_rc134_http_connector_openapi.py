from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

def test_rc130_rc134_routes_registered():
    paths = client.get("/openapi.json").json()["paths"]
    for path in [
        "/api/v1/http-connectors/clear",
        "/api/v1/http-connectors/robots-policy",
        "/api/v1/http-connectors/fixture-responses",
        "/api/v1/http-connectors/execute",
        "/api/v1/http-connectors/sla/{connector_id}",
    ]:
        assert path in paths
