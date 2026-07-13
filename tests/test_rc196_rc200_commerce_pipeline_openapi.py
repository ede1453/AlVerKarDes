from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

def test_rc196_rc200_routes_registered():
    paths = client.get("/openapi.json").json()["paths"]

    for path in [
        "/api/v1/commerce-pipeline/clear",
        "/api/v1/commerce-pipeline/run",
        "/api/v1/commerce-pipeline/runs",
        "/api/v1/commerce-pipeline/runs/{run_id}",
    ]:
        assert path in paths
