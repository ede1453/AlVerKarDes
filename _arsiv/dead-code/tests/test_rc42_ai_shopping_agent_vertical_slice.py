from fastapi.testclient import TestClient

from app.main import app
from tests.auth_test_helpers import auth_headers, internal_service_headers


def test_ai_shopping_agent_vertical_slice_event_and_decision():
    with TestClient(app) as client:
        headers = auth_headers(client)
        client.post(
            "/api/v1/events/clear",
            headers={**internal_service_headers(), **headers},
        )

        response = client.post(
            "/api/v1/ai-shopping-agent/run",
            headers=headers,
            json={
                "query": "MacBook Air",
                "user_id": "user-1",
                "profile": {
                    "preferred_marketplaces": ["saturn"],
                    "preferred_brands": ["Apple"],
                    "max_price": "1000.00",
                },
                "offers": [
                    {"id": "1", "marketplace": "amazon", "seller": "Amazon", "product_name": "Apple MacBook Air M3", "price": "999.00"},
                    {"id": "2", "marketplace": "saturn", "seller": "Saturn", "product_name": "Apple MacBook Air M3", "price": "949.00"},
                ],
            },
        )

        assert response.status_code == 200
        assert response.json()["decision"] == "BUY_NOW"

        event_response = client.get(
            "/api/v1/events?event_type=ai_shopping_agent.completed&source=ai_shopping_agent",
            headers={**internal_service_headers(), **headers},
        )
    assert event_response.status_code == 200
    assert event_response.json()["items"]
