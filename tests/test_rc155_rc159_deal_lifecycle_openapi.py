from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

def test_rc155_rc159_routes_registered():
    paths = client.get("/openapi.json").json()["paths"]
    for path in [
        "/api/v1/deal-lifecycle/clear",
        "/api/v1/deal-lifecycle/deals",
        "/api/v1/deal-lifecycle/deals/{deal_id}",
        "/api/v1/deal-lifecycle/deals/{deal_id}/decision-versions",
        "/api/v1/deal-lifecycle/deals/{deal_id}/transition",
        "/api/v1/deal-lifecycle/watch-policies",
        "/api/v1/deal-lifecycle/watch-policies/evaluate",
        "/api/v1/deal-lifecycle/events",
    ]:
        assert path in paths
