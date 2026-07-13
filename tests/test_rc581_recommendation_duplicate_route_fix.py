from collections import Counter

from fastapi.routing import APIRoute

from app.main import app


def test_rc581_recommendation_legacy_paths_are_registered_once():
    pairs = []
    for route in app.routes:
        if not isinstance(route, APIRoute):
            continue
        for method in route.methods or []:
            if method in {"HEAD", "OPTIONS"}:
                continue
            pairs.append((method, route.path))

    counts = Counter(pairs)

    assert counts[("POST", "/api/v1/recommendations/analyze")] == 1
    assert counts[("GET", "/api/v1/recommendations/sessions/{session_id}")] == 1


def test_rc581_recommendation_legacy_paths_use_api_v1_compat_router():
    analyze_routes = [
        route
        for route in app.routes
        if isinstance(route, APIRoute)
        and route.path == "/api/v1/recommendations/analyze"
        and "POST" in route.methods
    ]

    session_routes = [
        route
        for route in app.routes
        if isinstance(route, APIRoute)
        and route.path == "/api/v1/recommendations/sessions/{session_id}"
        and "GET" in route.methods
    ]

    assert len(analyze_routes) == 1
    assert len(session_routes) == 1
    assert analyze_routes[0].endpoint.__module__ == "app.api.v1.recommendations_router"
    assert session_routes[0].endpoint.__module__ == "app.api.v1.recommendations_router"
