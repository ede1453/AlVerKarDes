from collections import Counter

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_rc442_price_prediction_paths_exist_once_in_openapi():
    openapi = client.get("/openapi.json").json()
    paths = openapi["paths"]

    assert "/api/v1/price-prediction/predict" in paths
    assert "/api/v1/price-prediction/predict-cached" in paths
    assert "/api/v1/api/v1/price-prediction/predict" not in paths


def test_rc442_openapi_operation_ids_are_unique():
    openapi = client.get("/openapi.json").json()

    operation_ids = []
    for path_item in openapi["paths"].values():
        for operation in path_item.values():
            if isinstance(operation, dict) and "operationId" in operation:
                operation_ids.append(operation["operationId"])

    duplicates = [
        operation_id
        for operation_id, count in Counter(operation_ids).items()
        if count > 1
    ]

    assert duplicates == []
