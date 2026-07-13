from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _operation_id_for(path: str, method: str):
    openapi = client.get("/openapi.json").json()
    return openapi["paths"][path][method]["operationId"]


def test_rc522_legacy_analyze_operation_id_matches_snapshot_contract():
    assert (
        _operation_id_for("/api/v1/recommendations/analyze", "post")
        == "analyze_product_api_v1_recommendations_analyze_post"
    )


def test_rc522_legacy_session_operation_id_matches_snapshot_contract():
    assert (
        _operation_id_for("/api/v1/recommendations/sessions/{session_id}", "get")
        == "get_session_recommendations_api_v1_recommendations_sessions__session_id__get"
    )


def test_rc522_legacy_paths_still_work_after_operation_id_fix():
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
