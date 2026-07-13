from collections import Counter

from fastapi.routing import APIRoute
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_no_duplicate_api_route_method_path_pairs():
    method_path_pairs = []

    for route in app.routes:
        if not isinstance(route, APIRoute):
            continue

        for method in route.methods or []:
            if method in {"HEAD", "OPTIONS"}:
                continue
            method_path_pairs.append((method, route.path))

    duplicates = [
        pair
        for pair, count in Counter(method_path_pairs).items()
        if count > 1
    ]

    assert duplicates == []


def test_openapi_operation_ids_are_unique():
    response = client.get("/openapi.json")
    assert response.status_code == 200

    operation_ids = []

    for path_item in response.json()["paths"].values():
        for method, operation in path_item.items():
            if method.lower() not in {"get", "post", "put", "patch", "delete"}:
                continue

            operation_id = operation.get("operationId")
            if operation_id:
                operation_ids.append(operation_id)

    duplicates = [
        operation_id
        for operation_id, count in Counter(operation_ids).items()
        if count > 1
    ]

    assert duplicates == []


def test_trust_intelligence_routes_are_registered_once():
    route_pairs = [
        (method, route.path)
        for route in app.routes
        if isinstance(route, APIRoute)
        for method in (route.methods or [])
        if "/api/v1/trust-intelligence" in route.path and method not in {"HEAD", "OPTIONS"}
    ]

    counts = Counter(route_pairs)

    assert counts[("POST", "/api/v1/trust-intelligence/signals")] == 1
    assert counts[("GET", "/api/v1/trust-intelligence/profiles/{entity_type}/{entity_id}")] == 1
    assert counts[("POST", "/api/v1/trust-intelligence/evaluate")] == 1
