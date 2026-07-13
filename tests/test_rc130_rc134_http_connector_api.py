from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

def test_rc130_rc134_vertical_slice():
    client.post("/api/v1/http-connectors/clear")

    client.post(
        "/api/v1/http-connectors/robots-policy",
        json={
            "domain":"example.test",
            "allowed_paths":["/feed"],
            "crawl_delay_seconds":0,
        },
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
    )

    result = client.post(
        "/api/v1/http-connectors/execute",
        json={
            "connector_id":"example",
            "url":"https://example.test/feed",
            "cache_ttl_seconds":60,
        },
    )

    assert result.status_code == 200
    assert result.json()["executed"] is True

    sla = client.get(
        "/api/v1/http-connectors/sla/example"
    ).json()

    assert sla["request_count"] == 1
