from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

def test_rc206_rc210_routes_registered():
    paths = client.get("/openapi.json").json()["paths"]

    for path in [
        "/api/v1/deal-notifications/clear",
        "/api/v1/deal-notifications/preferences",
        "/api/v1/deal-notifications/preferences/{user_id}",
        "/api/v1/deal-notifications/build",
        "/api/v1/deal-notifications/{notification_id}/delivered",
        "/api/v1/deal-notifications",
    ]:
        assert path in paths
