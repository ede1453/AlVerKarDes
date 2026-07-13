from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

def test_rc221_rc240_vertical_slice():
    client.post("/api/v1/consumer-trust/clear")

    feedback = client.post(
        "/api/v1/consumer-trust/feedback",
        json={
            "payload":{
                "user_id":"u1",
                "recommendation_id":"r1",
                "feedback_type":"HELPFUL"
            }
        },
    ).json()
    assert feedback["recorded"] is True

    dashboard = client.post(
        "/api/v1/consumer-trust/trust-dashboard",
        json={
            "payload":{
                "recommendation_count":100,
                "audited_count":100,
                "passed_audit_count":95,
                "feedback_count":100,
                "helpful_feedback_count":90,
                "false_positive_count":2,
                "disclosure_compliance_pct":100
            }
        },
    ).json()
    assert dashboard["status"] == "EXCELLENT"
