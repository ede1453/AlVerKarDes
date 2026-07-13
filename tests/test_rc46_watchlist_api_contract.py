from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_watchlist_api_add_list_evaluate():
    client.post("/api/v1/watchlist/clear")

    add_response = client.post(
        "/api/v1/watchlist/items",
        json={
            "user_id": "user-1",
            "product_key": "macbook-air",
            "query": "MacBook Air",
            "target_price": "950.00",
        },
    )

    assert add_response.status_code == 200
    item = add_response.json()

    list_response = client.get("/api/v1/watchlist/users/user-1/items")
    assert list_response.status_code == 200
    assert len(list_response.json()["items"]) == 1

    evaluate_response = client.post(
        f"/api/v1/watchlist/items/{item['id']}/evaluate",
        json={
            "deal_detection": {"deal_level": "EXCELLENT_DEAL", "deal_score": 95},
            "price_prediction": {"recommendation_hint": "BUY_SOON"},
            "personalization": {"top_offer": {"personalization_score": 95}},
            "price_history": {"latest_price": "949.00"},
        },
    )

    assert evaluate_response.status_code == 200
    assert evaluate_response.json()["last_evaluation"]["target_reached"] is True


def test_watchlist_api_deactivate():
    add_response = client.post(
        "/api/v1/watchlist/items",
        json={
            "user_id": "user-2",
            "product_key": "iphone",
            "query": "iPhone",
        },
    )
    item = add_response.json()

    response = client.post(f"/api/v1/watchlist/items/{item['id']}/deactivate")

    assert response.status_code == 200
    assert response.json()["status"] == "INACTIVE"
