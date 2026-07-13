from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

def test_marketplace_vertical_slice():
    response = client.post(
        "/api/v1/marketplace-expansion/normalize",
        json={
            "marketplace": "amazon",
            "item": {
                "asin": "B0TEST123",
                "title": "Laptop",
                "detail_page_url": "https://amazon.test/item",
                "price": 999,
                "currency": "EUR",
            },
        },
    )
    assert response.status_code == 200
    assert response.json()["item"]["marketplace"] == "amazon"

    score = client.post(
        "/api/v1/marketplace-expansion/score",
        json={
            "current_price": 800,
            "historical_average_price": 1000,
            "store_trust_score": 90,
            "availability": "in_stock",
            "review_score": 4.5,
        },
    )
    assert score.status_code == 200
    assert score.json()["score"] > 0
