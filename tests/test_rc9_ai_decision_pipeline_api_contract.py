from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_ai_decision_pipeline_api_returns_final_decision():
    response = client.post(
        "/api/v1/ai-decision-pipeline/run",
        json={
            "deal_score": 95,
            "authenticity_score": 96,
            "recommendation": "BUY_NOW",
            "recommendation_confidence": 94,
            "trend_direction": "DOWN",
            "store_trust_score": 90,
            "stock_status": "in_stock",
            "reason_codes": ["HIGH_DEAL_SCORE", "AUTHENTIC_DISCOUNT"],
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["pipeline_status"] == "PASSED"
    assert data["final_decision"] == "BUY_NOW"
    assert data["risk_level"] == "LOW"
    assert len(data["stages"]) == 3
