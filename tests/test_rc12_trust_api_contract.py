from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_trust_intelligence_api_upserts_signal_and_evaluates():
    signal_response = client.post(
        "/api/v1/trust-intelligence/signals",
        json={
            "source_type": "store",
            "source_id": "store-api-1",
            "positive_count": 10,
            "negative_count": 0,
            "total_count": 10,
        },
    )

    assert signal_response.status_code == 200
    assert signal_response.json()["profile"]["trust_score"] == 100

    evaluation_response = client.post(
        "/api/v1/trust-intelligence/evaluate",
        json={
            "decision_id": "decision-api-1",
            "store_id": "store-api-1",
            "base_confidence": 90,
            "final_decision": "BUY_NOW",
        },
    )

    assert evaluation_response.status_code == 200
    data = evaluation_response.json()
    assert data["store_score"] == 100
    assert data["final_confidence"] > 90


def test_trust_intelligence_api_reads_profile():
    client.post(
        "/api/v1/trust-intelligence/signals",
        json={
            "source_type": "product",
            "source_id": "product-api-1",
            "positive_count": 7,
            "negative_count": 1,
            "total_count": 8,
        },
    )

    response = client.get("/api/v1/trust-intelligence/profiles/product/product-api-1")

    assert response.status_code == 200
    assert response.json()["entity_id"] == "product-api-1"
