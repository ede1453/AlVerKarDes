from collections import Counter

from fastapi.routing import APIRoute

from app.main import app


def test_connector_routes_are_registered_once():
    pairs = []

    for route in app.routes:
        if not isinstance(route, APIRoute):
            continue

        for method in route.methods or []:
            if method in {"HEAD", "OPTIONS"}:
                continue
            pairs.append((method, route.path))

    expected = [
        ("GET", "/api/v1/marketplace-connectors"),
        ("POST", "/api/v1/marketplace-connectors/search"),
        ("GET", "/api/v1/marketplace-connectors/ebay/health"),
        ("POST", "/api/v1/marketplace-connectors/ebay/search"),
        ("GET", "/api/v1/marketplace-connectors/idealo/health"),
        ("POST", "/api/v1/marketplace-connectors/idealo/feed"),
        ("POST", "/api/v1/marketplace-connectors/affiliate/click"),
        ("GET", "/api/v1/marketplace-connectors/affiliate/readiness"),
    ]

    counts = Counter(pairs)

    for pair in expected:
        assert counts[pair] == 1, pair
