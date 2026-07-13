from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_rc65_notification_routes_registered_once_in_openapi():
    paths = client.get("/openapi.json").json()["paths"]

    assert "/api/v1/notifications/deliver" in paths
    assert "/api/v1/notifications/from-smart-alert" in paths

    assert "post" in paths["/api/v1/notifications/deliver"]
    assert "post" in paths["/api/v1/notifications/from-smart-alert"]


def test_rc65_notification_operation_ids_are_stable():
    paths = client.get("/openapi.json").json()["paths"]

    deliver_operation = paths["/api/v1/notifications/deliver"]["post"]["operationId"]
    from_alert_operation = paths["/api/v1/notifications/from-smart-alert"]["post"]["operationId"]

    assert deliver_operation == "deliver_notification_api_v1_notifications_deliver_post"
    assert from_alert_operation == "deliver_notification_from_smart_alert_api_v1_notifications_from_smart_alert_post"
