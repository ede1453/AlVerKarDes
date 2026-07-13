from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_rc521_recommendation_legacy_analyze_path_exists_and_works():
    response = client.post(
        "/api/v1/recommendations/analyze",
        json={
            "query": "MacBook Air",
            "user_id": "user-1",
            "candidates": [
                {
                    "product_key": "macbook-air-saturn",
                    "product_name": "MacBook Air Saturn",
                    "marketplace": "saturn",
                    "price": "949.00",
                    "canonical_confidence": 95,
                }
            ],
            "deal_detection": {"deal_level": "EXCELLENT_DEAL"},
            "discount_intelligence": {
                "discount_quality": "EXCELLENT_REAL_DISCOUNT",
                "fake_discount_risk": "LOW",
            },
            "price_prediction": {"recommendation_hint": "BUY_SOON"},
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "COMPLETED"
    assert data["items"]
    assert data["run_id"]


def test_rc521_recommendation_legacy_session_path_returns_analyze_result():
    analyze_response = client.post(
        "/api/v1/recommendations/analyze",
        json={
            "query": "MacBook Air",
            "user_id": "user-1",
            "candidates": [
                {
                    "product_key": "macbook-air-saturn",
                    "product_name": "MacBook Air Saturn",
                    "marketplace": "saturn",
                    "price": "949.00",
                    "canonical_confidence": 95,
                }
            ],
        },
    )

    assert analyze_response.status_code == 200
    run_id = analyze_response.json()["run_id"]

    session_response = client.get(f"/api/v1/recommendations/sessions/{run_id}")

    assert session_response.status_code == 200
    assert session_response.json()["run_id"] == run_id


def test_rc521_recommendation_legacy_session_404_for_missing_id():
    response = client.get("/api/v1/recommendations/sessions/missing-session")

    assert response.status_code == 404
    assert response.json()["detail"] == "recommendation_session_not_found"


def test_rc521_recommendation_old_and_new_paths_exist_in_openapi():
    paths = client.get("/openapi.json").json()["paths"]

    assert "/api/v1/recommendations/analyze" in paths
    assert "/api/v1/recommendations/sessions/{session_id}" in paths
    assert "/api/v1/recommendations/recommend" in paths
    assert "/api/v1/recommendations/recommend-cached" in paths
