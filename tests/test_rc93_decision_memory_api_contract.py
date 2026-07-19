from fastapi.testclient import TestClient

from app.main import app
from tests.auth_test_helpers import auth_headers_and_user_id


def test_decision_memory_api_stores_and_reads_record():
    with TestClient(app) as client:
        headers, user_id = auth_headers_and_user_id(client)
        response = client.post(
            "/api/v1/decision-memory/store",
            headers=headers,
            json={
                "user_id": user_id,
                "product_id": "product-1",
                "offer_id": "offer-1",
                "final_decision": "BUY_NOW",
                "confidence": 94,
                "risk_level": "LOW",
                "opportunity_level": "HIGH",
                "deal_score": 95,
                "authenticity_score": 96,
                "recommendation": "BUY_NOW",
                "reason_codes": ["STRONG_BUY_SIGNAL"],
                "decision_context": {"context_id": "ctx-1"},
            },
        )

        assert response.status_code == 200
        saved = response.json()

        get_response = client.get(
            f"/api/v1/decision-memory/{saved['id']}", headers=headers
        )
    assert get_response.status_code == 200
    assert get_response.json()["id"] == saved["id"]


def test_decision_memory_api_evaluates_outcome():
    with TestClient(app) as client:
        headers, user_id = auth_headers_and_user_id(client)
        response = client.post(
            "/api/v1/decision-memory/store",
            headers=headers,
            json={
                "user_id": user_id,
                "final_decision": "BUY_NOW",
                "confidence": 94,
            },
        )
        saved = response.json()

        outcome_response = client.post(
            f"/api/v1/decision-memory/{saved['id']}/outcome",
            headers=headers,
            json={
                "decision_price": "100.00",
                "future_price": "120.00",
            },
        )

    assert outcome_response.status_code == 200
    assert outcome_response.json()["outcome"]["decision_correct"] is True
