from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.auth_core_router import router

def test_rc450_auth_core_openapi_paths():
    app = FastAPI()
    app.include_router(router, prefix="/api/v1")
    paths = TestClient(app).get("/openapi.json").json()["paths"]
    expected = [
        "/api/v1/auth/refresh",
        "/api/v1/auth/sessions",
        "/api/v1/auth/sessions/{session_id}",
        "/api/v1/auth/email-verification/issue",
        "/api/v1/auth/email-verification/confirm",
        "/api/v1/auth/password-reset/issue",
    ]
    for path in expected:
        assert path in paths
