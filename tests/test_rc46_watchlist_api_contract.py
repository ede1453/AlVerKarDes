from fastapi.testclient import TestClient

from app.main import app
from tests.auth_test_helpers import auth_headers_and_user_id


def test_watchlist_api_add_list_evaluate():
    with TestClient(app) as client:
        headers, user_id = auth_headers_and_user_id(client)

        # TEST-001 (2026-07-20): this call to the OPERATOR-only global
        # /watchlist/clear used to sit here, but a freshly-registered
        # SHOPPER (auth_headers_and_user_id) always gets a 403 from it --
        # confirmed empirically, it is a no-op for this test and was
        # removed. It never actually explained this test's 1st-observed
        # flake (see WIKI_ROOT Windows-Asyncpg-Xdist-Flaky-Test-Izleme.md);
        # that hypothesis was tested and falsified. The real hardening
        # below (asserting the specific item is present by id, rather than
        # an exact `len(items) == 1`) removes any residual dependency on
        # this user's list being otherwise empty, regardless of the actual
        # (still not conclusively identified) original cause.
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
        items = list_response.json()["items"]
        matching = [i for i in items if i["id"] == item["id"]]
        assert len(matching) == 1, f"expected item {item['id']} exactly once in {items}"

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
