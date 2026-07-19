"""CLIENT-001 (ADR-010): minimal static frontend served from /ui.

Regression test for a real, live-caught bug: the global CSP
(default-src 'none', HARDEN-004) silently blocked /ui's external
<script src>/<link> -- no console error, the page just never ran any JS
(confirmed via a real browser: click handlers never fired, form fell back
to a native GET submit). SecurityHeadersMiddleware now serves a relaxed,
still-restrictive CSP (default-src 'self', no 'unsafe-inline') only for
/ui paths; every other path keeps the original default-src 'none'.
"""

from fastapi.testclient import TestClient

from app.main import app


def test_ui_path_gets_relaxed_same_origin_csp():
    with TestClient(app) as client:
        response = client.get("/ui/")
    assert response.status_code == 200
    assert response.headers["content-security-policy"] == "default-src 'self'; frame-ancestors 'none'"
    # Still restrictive -- no inline script/style allowance.
    assert "unsafe-inline" not in response.headers["content-security-policy"]


def test_ui_static_assets_are_served_and_get_relaxed_csp():
    with TestClient(app) as client:
        css = client.get("/ui/style.css")
        js = client.get("/ui/app.js")
    assert css.status_code == 200
    assert js.status_code == 200
    assert css.headers["content-security-policy"] == "default-src 'self'; frame-ancestors 'none'"
    assert js.headers["content-security-policy"] == "default-src 'self'; frame-ancestors 'none'"


def test_api_paths_keep_the_original_strict_csp():
    # The regression this guards against: a path-based CSP override that's
    # too broad and accidentally weakens the API's own CSP.
    with TestClient(app) as client:
        response = client.get("/health")
    assert response.status_code == 200
    assert response.headers["content-security-policy"] == "default-src 'none'; frame-ancestors 'none'"


def test_root_path_keeps_the_original_strict_csp():
    with TestClient(app) as client:
        response = client.get("/")
    assert response.headers["content-security-policy"] == "default-src 'none'; frame-ancestors 'none'"
