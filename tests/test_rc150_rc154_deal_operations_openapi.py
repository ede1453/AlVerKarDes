from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

def test_rc150_rc154_routes_registered():
    paths = client.get("/openapi.json").json()["paths"]

    for path in [
        "/api/v1/deal-operations/clear",
        "/api/v1/deal-operations/watchlist",
        "/api/v1/deal-operations/evaluate",
        "/api/v1/deal-operations/opportunities/{opportunity_id}",
        "/api/v1/deal-operations/opportunities/{opportunity_id}/decisions",
    ]:
        assert path in paths
