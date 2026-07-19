import os

os.environ["AMAZON_CREATORS_FIXTURE_MODE"] = "true"
os.environ["AMAZON_CREATORS_PARTNER_TAG"] = "example-21"
os.environ["AMAZON_CREATORS_CLIENT_ID"] = "fixture-client"
os.environ["AMAZON_CREATORS_CLIENT_SECRET"] = "fixture-secret"

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_rc341_rc360_amazon_routes_registered():
    paths = client.get("/openapi.json").json()["paths"]

    for path in [
        "/api/v1/amazon-connector/health",
        "/api/v1/amazon-connector/metrics",
        "/api/v1/amazon-connector/search",
        "/api/v1/amazon-connector/items",
        "/api/v1/amazon-connector/collect",
    ]:
        assert path in paths
