from fastapi.testclient import TestClient

from app.main import app
from tests.auth_test_helpers import auth_headers_and_user_id, internal_service_headers


def test_watchlist_vertical_slice_from_smart_alert_stack():
    with TestClient(app) as client:
        headers, user_id = auth_headers_and_user_id(client)
        client.post(
            "/api/v1/events/clear",
            headers={**internal_service_headers(), **headers},
        )
        client.post("/api/v1/watchlist/clear", headers=headers)

        item_response = client.post(
            "/api/v1/watchlist/items",
            headers=headers,
            json={
                "user_id": user_id,
                "product_key": "macbook-air",
                "query": "MacBook Air",
                "target_price": "950.00",
                "channels": ["in_app"],
            },
        )
        assert item_response.status_code == 200
        item = item_response.json()

        deal_response = client.post(
            "/api/v1/deal-detection/detect",
            headers=headers,
            json={
                "product_key": "macbook-air",
                "offer": {"price": "949.00", "marketplace": "saturn"},
                "price_history": {"min_price": "949.00", "average_price": "999.00", "latest_price": "949.00", "trend": "DOWN"},
                "personalization": {"top_offer": {"personalization_score": 95}},
            },
        )
        assert deal_response.status_code == 200

        prediction_response = client.post(
            "/api/v1/price-prediction/predict",
            headers=headers,
            json={
                "product_key": "macbook-air",
                "price_history": {
                    "latest_price": "949.00",
                    "min_price": "949.00",
                    "average_price": "999.00",
                    "max_price": "1099.00",
                    "trend": "DOWN",
                    "points": [{"price": "999.00"}, {"price": "949.00"}],
                },
            },
        )
        assert prediction_response.status_code == 200

        eval_response = client.post(
            f"/api/v1/watchlist/items/{item['id']}/evaluate",
            headers=headers,
            json={
                "deal_detection": deal_response.json(),
                "price_prediction": prediction_response.json(),
                "personalization": {"top_offer": {"personalization_score": 95}},
                "price_history": {"latest_price": "949.00"},
            },
        )

        assert eval_response.status_code == 200
        assert eval_response.json()["last_evaluation"]["smart_alert"]["should_alert"] is True

        event_response = client.get(
            "/api/v1/events?event_type=watchlist.item_evaluated&source=watchlist",
            headers={**internal_service_headers(), **headers},
        )
    assert event_response.status_code == 200
    assert event_response.json()["items"]
