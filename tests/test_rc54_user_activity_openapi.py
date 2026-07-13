from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_user_activity_api_registered_in_openapi():
    paths = client.get("/openapi.json").json()["paths"]

    assert "/api/v1/user-activity/record" in paths
    assert "/api/v1/user-activity/users/{user_id}/events" in paths
    assert "/api/v1/user-activity/users/{user_id}/summary" in paths
    assert "/api/v1/user-activity/recommendations/adjust" in paths
    assert "/api/v1/api/v1/user-activity/record" not in paths
