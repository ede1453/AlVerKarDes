from fastapi.testclient import TestClient

from app.main import app
from tests.auth_test_helpers import operator_headers


def test_llm_audit_vertical_slice_from_gateway_response():
    request_payload = {
        "provider": "mock",
        "model": "mock-shopping-explainer",
        "system_prompt": "Explain safely.",
        "user_prompt": "Explain BUY_NOW.",
        "guardrails": ["Do not change assistant_decision."],
        "structured_context": {
            "assistant_decision": "BUY_NOW",
            "assistant_context": {
                "product_name": "MacBook Air",
            },
        },
    }

    with TestClient(app) as client:
        headers = operator_headers(client)

        gateway_response = client.post(
            "/api/v1/llm-gateway/generate",
            headers=headers,
            json=request_payload,
        )

        assert gateway_response.status_code == 200

        audit_response = client.post(
            "/api/v1/llm-audit-traces",
            headers=headers,
            json={
                "request_payload": request_payload,
                "gateway_response": gateway_response.json(),
            },
        )

    assert audit_response.status_code == 200

    trace = audit_response.json()

    assert trace["status"] == "COMPLETED"
    assert trace["assistant_decision"] == "BUY_NOW"
    assert len(trace["prompt_hash"]) == 64
