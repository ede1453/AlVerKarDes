from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_decision_context_api_builds_context():
    response = client.post(
        "/api/v1/decision-context/build",
        json={
            "product_id": "product-1",
            "offer_id": "offer-1",
            "deal_score": 95,
            "authenticity_score": 96,
            "recommendation": "BUY_NOW",
            "recommendation_confidence": 94,
            "final_decision": "BUY_NOW",
            "risk_level": "LOW",
            "opportunity_level": "HIGH",
            "reason_codes": ["HIGH_DEAL_SCORE"],
            "explanation": ["Deal score is high."],
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["context_id"].startswith("decision-context::offer-1::")
    assert data["decision"]["final_decision"] == "BUY_NOW"
    assert data["market"]["country"] == "DE"
