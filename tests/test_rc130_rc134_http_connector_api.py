from fastapi.testclient import TestClient

from app.main import app
from tests.auth_test_helpers import internal_service_headers

client = TestClient(app)

def test_rc130_rc134_vertical_slice():
    client.post("/api/v1/http-connectors/clear", headers=internal_service_headers())

    client.post(
        "/api/v1/http-connectors/robots-policy",
        json={
            "domain":"example.test",
            "allowed_paths":["/feed"],
            "crawl_delay_seconds":0,
        },
        headers=internal_service_headers(),
    )

    client.post(
        "/api/v1/http-connectors/fixture-responses",
        json={
            "url":"https://example.test/feed",
            "status_code":200,
            "headers":{"content-type":"application/json"},
            "body":"{\"items\":[]}",
            "elapsed_ms":25,
        },
        headers=internal_service_headers(),
    )

    result = client.post(
        "/api/v1/http-connectors/execute",
        json={
            "connector_id":"example",
            "url":"https://example.test/feed",
            "cache_ttl_seconds":60,
        },
        headers=internal_service_headers(),
    )

    assert result.status_code == 200
    assert result.json()["executed"] is True

    sla = client.get(
        "/api/v1/http-connectors/sla/example",
        headers=internal_service_headers(),
    ).json()

    assert sla["request_count"] == 1
