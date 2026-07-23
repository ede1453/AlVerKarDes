from fastapi.testclient import TestClient

from app.main import app
from tests.auth_test_helpers import operator_headers


def test_llm_explanation_vertical_slice_from_assistant_style_card():
    # VISION-002 (ADR-019): this used to call ai_shopping_assistant's
    # /advise to build a realistic "assistant card" payload before feeding
    # it to llm_explanation -- ai_shopping_assistant was archived (no
    # production caller), but its actual real (fully deterministic) output
    # for this exact scenario was captured before archiving and is
    # reproduced directly here, so llm_explanation's own vertical slice
    # coverage (same scenario, same expected prompt content) is unchanged.
    assistant_data = {
        "assistant_decision": "BUY_NOW",
        "headline": "Buy MacBook Air now",
        "summary": "The combined decision, personalization, and trust signals support buying now.",
        "confidence": 94,
        "risk_level": "LOW",
        "opportunity_level": "HIGH",
        "next_actions": [
            "Check final seller terms before purchase.",
            "Confirm warranty, return policy, and delivery cost.",
            "Buy only if the checkout price matches the detected offer.",
        ],
        "reason_codes": ["STRONG_BUY_SIGNAL", "ASSISTANT_BUY_SIGNAL"],
        "explanation": ["Trust intelligence was included in the assistant decision."],
        "assistant_context": {
            "user_id": "user-1",
            "query": "Should I buy this MacBook?",
            "product_name": "MacBook Air",
            "product_brand": "apple",
            "product_category": None,
            "current_price": "849.00",
            "currency": "EUR",
            "base_decision": "BUY_NOW",
            "personalized_decision": None,
            "trust_score": 90,
            "community_score": 88,
            "metadata": {},
        },
    }

    with TestClient(app) as client:
        headers = operator_headers(client)
        explanation_response = client.post(
            "/api/v1/llm-explanations/prepare",
            headers=headers,
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
