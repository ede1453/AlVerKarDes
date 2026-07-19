from fastapi.testclient import TestClient

from app.main import app
from tests.auth_test_helpers import auth_headers, internal_service_headers


def test_ai_explanation_vertical_slice_from_agent_deal_discount_alert():
    with TestClient(app) as client:
        headers = auth_headers(client)
        client.post(
            "/api/v1/events/clear",
            headers={**internal_service_headers(), **headers},
        )

        agent = {
            "decision": "BUY_NOW",
            "confidence": 90,
        }
        deal = {
            "deal_level": "EXCELLENT_DEAL",
            "deal_score": 95,
        }
        discount = {
            "discount_quality": "EXCELLENT_REAL_DISCOUNT",
            "fake_discount_risk": "LOW",
        }
        alert = {
            "alert_level": "URGENT",
            "should_alert": True,
        }
        prediction = {
            "recommendation_hint": "BUY_SOON",
        }

        response = client.post(
            "/api/v1/ai-explanation/explain",
            headers=headers,
            json={
                "agent_decision": agent,
                "deal_detection": deal,
                "discount_intelligence": discount,
                "smart_alert": alert,
                "price_prediction": prediction,
            },
        )

        assert response.status_code == 200
        assert response.json()["next_actions"]

        event_response = client.get(
            "/api/v1/events?event_type=ai_explanation.generated&source=ai_explanation",
            headers={**internal_service_headers(), **headers},
        )
    assert event_response.status_code == 200
    assert event_response.json()["items"]
