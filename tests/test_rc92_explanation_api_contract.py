from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_explanation_api_generates_explanation():
    response = client.post(
        "/api/v1/explanations/generate",
        json={
            "final_decision": "BUY_NOW",
            "confidence": 94,
            "risk_level": "LOW",
            "opportunity_level": "HIGH",
            "reason_codes": ["STRONG_BUY_SIGNAL"],
            "scores": {"deal_score": 95, "authenticity_score": 96},
            "market": {"country": "DE", "currency": "EUR"},
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["headline"] == "Buy now"
    assert data["llm_prompt_context"]["final_decision"] == "BUY_NOW"
