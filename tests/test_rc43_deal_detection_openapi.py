from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_deal_detection_api_registered_in_openapi():
    paths = client.get("/openapi.json").json()["paths"]

    assert "/api/v1/deal-detection/detect" in paths
    assert "/api/v1/deal-detection/detect-cached" in paths
    assert "/api/v1/api/v1/deal-detection/detect" not in paths
