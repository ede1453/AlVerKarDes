from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_llm_explanation_api_prepares_prompt():
    response = client.post(
        "/api/v1/llm-explanations/prepare",
        json={
            "assistant_decision": "BUY_NOW",
            "headline": "Buy MacBook Air now",
            "summary": "The combined decision supports buying now.",
            "confidence": 94,
            "risk_level": "LOW",
            "opportunity_level": "HIGH",
            "next_actions": ["Check final seller terms before purchase."],
            "reason_codes": ["ASSISTANT_BUY_SIGNAL"],
            "assistant_context": {"product_name": "MacBook Air"},
            "language": "en",
            "tone": "clear",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["mode"] == "PROMPT_READY"
    assert data["prompt"]["structured_context"]["assistant_decision"] == "BUY_NOW"
    assert "Do not change assistant_decision." in data["prompt"]["guardrails"]
