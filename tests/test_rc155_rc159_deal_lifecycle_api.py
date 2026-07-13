from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

def test_rc155_rc159_vertical_slice():
    client.post("/api/v1/deal-lifecycle/clear")

    registered = client.post(
        "/api/v1/deal-lifecycle/deals",
        json={
            "source_id":"amazon",
            "external_offer_id":"offer-1",
            "canonical_product_key":"product-1",
            "observed_at":"2026-07-12T10:00:00+00:00",
            "price":899,
            "currency":"EUR"
        },
    )
    assert registered.status_code == 200
    deal_id = registered.json()["deal"]["deal_id"]

    version = client.post(
        f"/api/v1/deal-lifecycle/deals/{deal_id}/decision-versions",
        json={
            "decision":"BUY",
            "confidence":85,
            "explanation":"Strong deal",
            "evidence":{"discount":25}
        },
    )
    assert version.json()["stored"] is True

    transition = client.post(
        f"/api/v1/deal-lifecycle/deals/{deal_id}/transition",
        json={
            "new_status":"VALIDATED",
            "reason":"Checks passed"
        },
    )
    assert transition.json()["transitioned"] is True

    events = client.get(
        "/api/v1/deal-lifecycle/events",
        params={"deal_id":deal_id},
    ).json()
    assert events["event_count"] == 3
