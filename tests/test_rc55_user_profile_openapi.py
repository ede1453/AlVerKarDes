from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_user_profile_api_registered_in_openapi():
    paths = client.get("/openapi.json").json()["paths"]

    assert "/api/v1/user-profiles/{user_id}" in paths
    assert "/api/v1/user-profiles/preferences" in paths
    assert "/api/v1/user-profiles/feedback/merge" in paths
    assert "/api/v1/user-profiles/{user_id}/recommendation-context" in paths
    assert "/api/v1/api/v1/user-profiles/{user_id}" not in paths
