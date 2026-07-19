from fastapi.testclient import TestClient

from app.main import app
from tests.auth_test_helpers import auth_headers_and_user_id


def test_watchlist_api_add_list_evaluate():
    with TestClient(app) as client:
        headers, user_id = auth_headers_and_user_id(client)

        client.post("/api/v1/watchlist/clear", headers=headers)

        add_response = client.post(
            "/api/v1/watchlist/items",
            headers=headers,
            json={
                "user_id": user_id,
                "product_key": "macbook-air",
                "query": "MacBook Air",
                "target_price": "950.00",
            },
        )

        assert add_response.status_code == 200
        item = add_response.json()

        list_response = client.get(
            f"/api/v1/watchlist/users/{user_id}/items", headers=headers
        )
        assert list_response.status_code == 200
        assert len(list_response.json()["items"]) == 1

        evaluate_response = client.post(
            f"/api/v1/watchlist/items/{item['id']}/evaluate",
            headers=headers,
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
    with TestClient(app) as client:
        headers, user_id = auth_headers_and_user_id(client)

        add_response = client.post(
            "/api/v1/watchlist/items",
            headers=headers,
            json={
                "user_id": user_id,
                "product_key": "iphone",
                "query": "iPhone",
            },
        )
        item = add_response.json()

        response = client.post(
            f"/api/v1/watchlist/items/{item['id']}/deactivate", headers=headers
        )

    assert response.status_code == 200
    assert response.json()["status"] == "INACTIVE"
