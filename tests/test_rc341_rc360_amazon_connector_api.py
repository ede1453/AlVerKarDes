import os

os.environ["AMAZON_CREATORS_FIXTURE_MODE"] = "true"
os.environ["AMAZON_CREATORS_PARTNER_TAG"] = "example-21"
os.environ["AMAZON_CREATORS_CLIENT_ID"] = "fixture-client"
os.environ["AMAZON_CREATORS_CLIENT_SECRET"] = "fixture-secret"

from fastapi.testclient import TestClient

from app.main import app
from tests.auth_test_helpers import internal_service_headers

client = TestClient(app)


def test_rc341_rc360_amazon_vertical_slice():
    response = client.post(
        "/api/v1/amazon-connector/collect",
        json={
            "keywords":"laptop",
            "page_size":10,
            "filters":{}
        },
        headers=internal_service_headers(),
    )

    assert response.status_code == 200
    data = response.json()

    assert data["executed"] is True
    assert data["item_count"] == 1
    assert data["snapshot_count"] == 1
