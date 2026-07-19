from fastapi.testclient import TestClient

from app.main import app
from tests.auth_test_helpers import internal_service_headers

client = TestClient(app)

def test_rc115_rc119_vertical_slice():
    client.post("/api/v1/connector-runtime/clear", headers=internal_service_headers())
    result = client.post(
        "/api/v1/connector-runtime/execute",
        json={
            "source_id": "amazon-de",
            "adapter_type": "fixture_json",
            "source_config": {
                "fixture_path": "tests/fixtures/commerce_ingestion/amazon_de_sample.json"
            }
        },
        headers=internal_service_headers(),
    )
    assert result.status_code == 200
    data = result.json()
    assert data["executed"] is True
    run_id = data["run"]["run_id"]

    run = client.get(
        f"/api/v1/connector-runtime/runs/{run_id}",
        headers=internal_service_headers(),
    )
    assert run.status_code == 200

    history = client.get(
        "/api/v1/connector-runtime/price-history/apple::macbook-air::m5::16gb::512gb",
        headers=internal_service_headers(),
    ).json()
    assert history["price_point_count"] == 2

    events = client.get(
        "/api/v1/connector-runtime/events",
        params={"run_id": run_id},
        headers=internal_service_headers(),
    ).json()
    assert events["event_count"] == 2
