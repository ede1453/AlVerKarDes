from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_decision_memory_api_stores_and_reads_record():
    response = client.post(
        "/api/v1/decision-memory/store",
        json={
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

    get_response = client.get(f"/api/v1/decision-memory/{saved['id']}")
    assert get_response.status_code == 200
    assert get_response.json()["id"] == saved["id"]


def test_decision_memory_api_evaluates_outcome():
    response = client.post(
        "/api/v1/decision-memory/store",
        json={
            "final_decision": "BUY_NOW",
            "confidence": 94,
        },
    )
    saved = response.json()

    outcome_response = client.post(
        f"/api/v1/decision-memory/{saved['id']}/outcome",
        json={
            "decision_price": "100.00",
            "future_price": "120.00",
        },
    )

    assert outcome_response.status_code == 200
    assert outcome_response.json()["outcome"]["decision_correct"] is True
