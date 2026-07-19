from fastapi.testclient import TestClient

from app.main import app
from tests.auth_test_helpers import operator_headers

client = TestClient(app)


def test_rc90_vertical_slice_complete_readiness_certification():
    with TestClient(app) as client:
        headers = operator_headers(client)
        required_checks = [
            "openapi_contract",
            "schema_contract",
            "database_migrations",
            "runtime_health",
            "security_review",
        ]

        for check_name in required_checks:
            response = client.post(
                "/api/v1/notification-outbox/readiness/checks",
                headers=headers,
                json={
                    "check_name": check_name,
                    "passed": True,
                    "details": f"{check_name} passed",
                },
            )
            assert response.status_code == 200
            assert response.json()["updated"] is True

        result = client.get(
            "/api/v1/notification-outbox/readiness/status",
            headers=headers,
        ).json()

    assert result["status"] == "READY"
    assert result["passed_check_count"] == 5
    assert result["failed_check_count"] == 0
