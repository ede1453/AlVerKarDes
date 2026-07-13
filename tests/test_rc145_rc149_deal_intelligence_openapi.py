from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

def test_rc145_rc149_routes_registered():
    paths = client.get("/openapi.json").json()["paths"]
    for path in [
        "/api/v1/deal-intelligence/history",
        "/api/v1/deal-intelligence/discount-truth",
        "/api/v1/deal-intelligence/confidence",
        "/api/v1/deal-intelligence/rank",
        "/api/v1/deal-intelligence/recommendation",
        "/api/v1/deal-intelligence/evaluate",
    ]:
        assert path in paths
