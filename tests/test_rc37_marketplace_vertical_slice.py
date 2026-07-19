from fastapi.testclient import TestClient

from app.main import app
from tests.auth_test_helpers import internal_service_headers

client = TestClient(app)


def test_marketplace_vertical_slice_aggregate_cache_event():
    client.post("/api/v1/events/clear", headers=internal_service_headers())

    response = client.post("/api/v1/marketplace-aggregation/aggregate-cached", json={
        "query": "MacBook Air",
        "offers": [
            {"marketplace": "amazon", "seller": "Amazon", "product_name": "MacBook Air M3", "price": "999.00", "currency": "EUR"},
            {"marketplace": "saturn", "seller": "Saturn", "product_name": "MacBook Air M3", "price": "949.00", "currency": "EUR"},
        ],
        "ttl_seconds": 300,
    })

    assert response.status_code == 200
    assert response.json()["value"]["offer_count"] == 2

    event_response = client.get(
        "/api/v1/events?event_type=marketplace.aggregation.completed&source=marketplace_aggregation",
        headers=internal_service_headers(),
    )
    assert event_response.status_code == 200
    assert event_response.json()["items"]
