from fastapi.testclient import TestClient

from app.main import app
from tests.auth_test_helpers import auth_headers


def test_deal_detection_vertical_slice_from_ai_shopping_agent():
    with TestClient(app) as client:
        headers = auth_headers(client)
        agent_response = client.post(
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

        assert agent_response.status_code == 200
        agent = agent_response.json()

        deal_response = client.post(
            "/api/v1/deal-detection/detect",
            headers=headers,
            json={
                "product_key": agent["price_history"]["product_key"],
                "offer": agent["top_offer"],
                "price_history": agent["price_history"],
                "personalization": agent["personalization"],
            },
        )

    assert deal_response.status_code == 200
    assert deal_response.json()["deal_score"] >= 70
