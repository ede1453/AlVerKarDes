from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_watchlist_api_registered_in_openapi():
    paths = client.get("/openapi.json").json()["paths"]

    assert "/api/v1/watchlist/items" in paths
    assert "/api/v1/watchlist/users/{user_id}/items" in paths
    assert "/api/v1/watchlist/items/{item_id}" in paths
    assert "/api/v1/watchlist/items/{item_id}/evaluate" in paths
    assert "/api/v1/api/v1/watchlist/items" not in paths
