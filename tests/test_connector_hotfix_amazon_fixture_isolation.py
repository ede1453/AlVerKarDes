from fastapi.testclient import TestClient

from app.main import app
from tests.auth_test_helpers import internal_service_headers

client = TestClient(app)


def test_amazon_router_uses_current_environment(
    monkeypatch,
):
    monkeypatch.setenv(
        "AMAZON_CREATORS_FIXTURE_MODE",
        "true",
    )
    monkeypatch.setenv(
        "AMAZON_CREATORS_PARTNER_TAG",
        "example-21",
    )
    monkeypatch.setenv(
        "AMAZON_CREATORS_CLIENT_ID",
        "fixture-client",
    )
    monkeypatch.setenv(
        "AMAZON_CREATORS_CLIENT_SECRET",
        "fixture-secret",
    )
    monkeypatch.setenv(
        "AMAZON_CREATORS_FIXTURE_PATH",
        "fixtures/amazon/search_response.json",
    )

    response = client.post(
        "/api/v1/amazon-connector/collect",
        json={
            "keywords": "laptop",
            "page_size": 10,
            "filters": {},
        },
        headers=internal_service_headers(),
    )

    assert response.status_code == 200
    data = response.json()

    assert data["executed"] is True
    assert data["item_count"] >= 1
