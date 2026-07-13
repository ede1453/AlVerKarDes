from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_llm_explanation_vertical_slice_from_assistant_card():
    assistant_response = client.post(
        "/api/v1/ai-shopping-assistant/advise",
        json={
            "user_id": "user-1",
            "query": "Should I buy this MacBook?",
            "product_name": "MacBook Air",
            "product_brand": "apple",
            "current_price": "849.00",
            "currency": "EUR",
            "final_decision": "BUY_NOW",
            "confidence": 94,
            "risk_level": "LOW",
            "opportunity_level": "HIGH",
            "reason_codes": ["STRONG_BUY_SIGNAL"],
            "trust_score": 90,
            "community_score": 88,
        },
    )

    assert assistant_response.status_code == 200
    assistant_data = assistant_response.json()

    explanation_response = client.post(
        "/api/v1/llm-explanations/prepare",
        json={
            **assistant_data,
            "language": "en",
            "tone": "clear",
        },
    )

    assert explanation_response.status_code == 200

    data = explanation_response.json()

    assert data["mode"] == "PROMPT_READY"
    assert data["prompt"]["structured_context"]["assistant_decision"] == "BUY_NOW"
    assert "MacBook Air" in data["prompt"]["user_prompt"]
