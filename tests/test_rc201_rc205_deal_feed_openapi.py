from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

def test_rc201_rc205_routes_registered():
    paths = client.get("/openapi.json").json()["paths"]

    for path in [
        "/api/v1/deal-feed/clear",
        "/api/v1/deal-feed/ingest",
        "/api/v1/deal-feed/query",
        "/api/v1/deal-feed/deals/{deal_id}",
    ]:
        assert path in paths
