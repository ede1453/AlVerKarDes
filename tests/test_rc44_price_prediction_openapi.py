from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_price_prediction_api_registered_in_openapi():
    paths = client.get("/openapi.json").json()["paths"]

    assert "/api/v1/price-prediction/predict" in paths
    assert "/api/v1/price-prediction/predict-cached" in paths
    assert "/api/v1/api/v1/price-prediction/predict" not in paths
