from fastapi.testclient import TestClient

from app.main import app
from tests.auth_test_helpers import auth_headers


def test_ai_explanation_api_explains_decision():
    with TestClient(app) as client:
        headers = auth_headers(client)
        response = client.post(
            "/api/v1/ai-explanation/explain",
            headers=headers,
            json={
                "language": "en",
                "tone": "clear",
                "agent_decision": {"decision": "BUY_NOW"},
                "deal_detection": {"deal_level": "EXCELLENT_DEAL"},
                "discount_intelligence": {"discount_quality": "EXCELLENT_REAL_DISCOUNT", "fake_discount_risk": "LOW"},
                "smart_alert": {"alert_level": "URGENT"},
                "price_prediction": {"recommendation_hint": "BUY_SOON"},
            },
        )

    assert response.status_code == 200
    assert response.json()["headline"] == "This looks like a strong buy opportunity"


def test_ai_explanation_cached_api_returns_cache_metadata():
    with TestClient(app) as client:
        headers = auth_headers(client)
        response = client.post(
            "/api/v1/ai-explanation/explain-cached",
            headers=headers,
            json={
                "agent_decision": {"decision": "BUY_NOW"},
                "ttl_seconds": 300,
            },
        )

    assert response.status_code == 200
    assert "cache_hit" in response.json()
