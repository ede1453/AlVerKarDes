from fastapi.testclient import TestClient

from app.main import app
from tests.auth_test_helpers import operator_headers

client = TestClient(app)


def test_llm_gateway_vertical_slice_from_prepared_explanation():
    with TestClient(app) as scoped_client:
        headers = operator_headers(scoped_client)
        prepared_response = scoped_client.post(
            "/api/v1/llm-explanations/prepare",
            headers=headers,
            json={
                "assistant_decision": "BUY_NOW",
                "headline": "Buy MacBook Air now",
                "summary": "The combined decision supports buying now.",
                "confidence": 94,
                "next_actions": ["Check final seller terms before purchase."],
                "reason_codes": ["ASSISTANT_BUY_SIGNAL"],
                "assistant_context": {
                    "product_name": "MacBook Air",
                },
            },
        )

        assert prepared_response.status_code == 200
        prepared = prepared_response.json()

        gateway_response = scoped_client.post(
            "/api/v1/llm-gateway/generate",
            headers=headers,
            json={
                "provider": "mock",
                "model": "mock-shopping-explainer",
                "system_prompt": prepared["prompt"]["system_prompt"],
                "user_prompt": prepared["prompt"]["user_prompt"],
                "guardrails": prepared["prompt"]["guardrails"],
                "structured_context": prepared["prompt"]["structured_context"],
            },
        )

    assert gateway_response.status_code == 200

    data = gateway_response.json()

    assert data["status"] == "COMPLETED"
    assert "MacBook Air" in data["generated_text"]
    assert data["usage"]["mock"] is True
