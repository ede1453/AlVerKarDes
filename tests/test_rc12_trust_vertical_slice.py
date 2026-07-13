from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_trust_intelligence_vertical_slice_applies_feedback_adjustment():
    client.post(
        "/api/v1/trust-intelligence/signals",
        json={
            "source_type": "community",
            "source_id": "global",
            "positive_count": 20,
            "negative_count": 0,
            "total_count": 20,
        },
    )

    response = client.post(
        "/api/v1/trust-intelligence/evaluate",
        json={
            "decision_id": "decision-vs-1",
            "community_id": "global",
            "base_confidence": 80,
            "final_decision": "BUY_NOW",
            "feedback_summary": {
                "confidence_adjustment": 4,
            },
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["community_score"] == 100
    assert data["final_confidence"] > 80
    assert "FEEDBACK_LEARNING_ADJUSTMENT" in data["reason_codes"]
