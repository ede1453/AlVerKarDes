from fastapi.testclient import TestClient

from app.main import app
from tests.auth_test_helpers import operator_headers

def test_rc221_rc240_vertical_slice():
    with TestClient(app) as client:
        headers = operator_headers(client)
        client.post("/api/v1/consumer-trust/clear", headers=headers)

        feedback = client.post(
            "/api/v1/consumer-trust/feedback",
            headers=headers,
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
            headers=headers,
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
