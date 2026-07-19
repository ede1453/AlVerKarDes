from fastapi.testclient import TestClient

from app.main import app
from tests.auth_test_helpers import operator_headers


def test_rc301_rc340_vertical_slice():
    with TestClient(app) as client:
        headers = operator_headers(client)
        client.post("/api/v1/production-launch/clear", headers=headers)

        db = client.post(
            "/api/v1/production-launch/database-config",
            headers=headers,
            json={
                "payload":{
                    "database_url":"postgresql://user:pass@db/app"
                }
            },
        )
        assert db.status_code == 200
        assert db.json()["result"]["valid"] is True

        manifest = client.post(
            "/api/v1/production-launch/release-manifest",
            headers=headers,
            json={
                "payload":{
                    "version":"v1.0.0",
                    "commit_sha":"abc123",
                    "image_digest":"sha256:def",
                    "go_no_go_decision":"GO"
                }
            },
        )
    assert manifest.status_code == 200
    assert manifest.json()["result"]["manifest"]["publishable"] is True
