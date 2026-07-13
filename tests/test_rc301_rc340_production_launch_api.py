from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_rc301_rc340_vertical_slice():
    client.post("/api/v1/production-launch/clear")

    db = client.post(
        "/api/v1/production-launch/database-config",
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
