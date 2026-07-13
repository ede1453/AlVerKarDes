
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

def test_rc79_openapi_contains_batch_summary_endpoint():
    paths = client.get("/openapi.json").json()["paths"]
    assert "/api/v1/notification-outbox/batch-summary" in paths
