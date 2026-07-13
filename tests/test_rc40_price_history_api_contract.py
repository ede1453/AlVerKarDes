from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_price_history_api_bulk_add_and_summary():
    client.post("/api/v1/price-history/clear")

    response = client.post(
        "/api/v1/price-history/points/bulk",
        json={
            "points": [
                {"product_key": "macbook-air", "marketplace": "amazon", "price": "999.00", "currency": "EUR"},
                {"product_key": "macbook-air", "marketplace": "saturn", "price": "949.00", "currency": "EUR"},
            ]
        },
    )

    assert response.status_code == 200
    assert response.json()["added_count"] == 2

    summary_response = client.get("/api/v1/price-history/macbook-air/summary")

    assert summary_response.status_code == 200
    summary = summary_response.json()
    assert summary["point_count"] == 2
    assert summary["trend"] == "DOWN"


def test_price_history_summary_cached_api_returns_cache_metadata():
    response = client.post(
        "/api/v1/price-history/summary-cached",
        json={"product_key": "macbook-air", "ttl_seconds": 300},
    )

    assert response.status_code == 200
    assert "cache_hit" in response.json()
