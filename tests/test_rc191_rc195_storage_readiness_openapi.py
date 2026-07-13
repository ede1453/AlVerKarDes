from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

def test_rc191_rc195_routes_registered():
    paths = client.get("/openapi.json").json()["paths"]

    for path in [
        "/api/v1/storage-production-readiness/clear",
        "/api/v1/storage-production-readiness/capacity",
        "/api/v1/storage-production-readiness/encryption-policies",
        "/api/v1/storage-production-readiness/encryption-compliance",
        "/api/v1/storage-production-readiness/access-events",
        "/api/v1/storage-production-readiness/maintenance-windows",
        "/api/v1/storage-production-readiness/maintenance-windows/evaluate",
        "/api/v1/storage-production-readiness/readiness",
        "/api/v1/storage-production-readiness/readiness/latest",
    ]:
        assert path in paths
