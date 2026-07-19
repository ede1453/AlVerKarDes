from fastapi.testclient import TestClient

from app.main import app
from tests.auth_test_helpers import auth_headers


def test_ai_shopping_assistant_vertical_slice_buy_now_card():
    with TestClient(app) as client:
        headers = auth_headers(client)
        response = client.post(
            "/api/v1/ai-shopping-assistant/advise",
            headers=headers,
            json={
                "user_id": "user-vertical-1",
                "query": "Is this deal safe?",
                "product_name": "MacBook Air",
                "final_decision": "BUY_NOW",
                "confidence": 94,
                "risk_level": "LOW",
                "opportunity_level": "HIGH",
                "reason_codes": [
                    "STRONG_BUY_SIGNAL",
                    "TRUSTED_STORE",
                    "POSITIVE_USER_FEEDBACK",
                ],
                "explanation": [
                    "Deal score and authenticity score are both high.",
                    "Trust intelligence was positive.",
                ],
                "personalized_decision": "BUY_NOW",
                "personalized_confidence": 96,
                "personalization_reasons": ["USER_PREFERS_BRAND"],
                "trust_score": 92,
                "community_score": 89,
            },
        )

    assert response.status_code == 200

    data = response.json()

    assert data["assistant_decision"] == "BUY_NOW"
    assert data["confidence"] == 96
    assert "USER_PREFERS_BRAND" in data["reason_codes"]
    assert "ASSISTANT_BUY_SIGNAL" in data["reason_codes"]
    assert data["assistant_context"]["community_score"] == 89
