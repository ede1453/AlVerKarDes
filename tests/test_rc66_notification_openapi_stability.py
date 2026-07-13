from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_rc66_notification_openapi_request_schema_is_stable():
    paths = client.get("/openapi.json").json()["paths"]

    deliver = paths["/api/v1/notifications/deliver"]["post"]
    from_alert = paths["/api/v1/notifications/from-smart-alert"]["post"]

    assert "requestBody" in deliver
    assert "responses" in deliver
    assert "requestBody" in from_alert
    assert "responses" in from_alert

    assert "200" in deliver["responses"]
    assert "200" in from_alert["responses"]
