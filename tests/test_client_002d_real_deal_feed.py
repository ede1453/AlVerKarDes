"""CLIENT-002d (ADR-011/ADR-012 follow-up): POST /deal-feed/query now reads
REAL ingested market.Price data via RealDealFeedSourceService, closing
WIKI_ROOT/07-Issues-Risks/Deal-Feed-Kopuk-Veri-Kaynagi-CLIENT-002b (the
endpoint used to be backed entirely by an in-memory store only reachable
via POST /deal-feed/ingest, disconnected from real ingestion).

DealFeedBuilder's dedup/personalization-scoring algorithm itself is
unchanged and still covered by tests/test_rc205_deal_feed_service.py --
these tests cover the new real-data bridge only.
"""

import uuid

from fastapi.testclient import TestClient

from app.main import app
from tests.auth_test_helpers import internal_service_headers, operator_headers


def _ingest_real_product(client: TestClient, *, price: float):
    product_name = f"CLIENT-002d Real Deal {uuid.uuid4().hex[:8]}"
    create = client.post(
        "/api/v1/products/from-name",
        params={"product_name": product_name, "country": "DE"},
        headers=operator_headers(client),
    )
    assert create.status_code == 201, create.text
    product_id = create.json()["id"]

    store = client.post(
        "/api/v1/market/stores",
        json={"name": "CLIENT-002d Store", "slug": f"client-002d-{uuid.uuid4().hex[:8]}", "country": "DE"},
        headers=internal_service_headers(),
    )
    assert store.status_code == 201, store.text
    store_id = store.json()["id"]

    offer = client.post(
        "/api/v1/market/offers",
        json={"product_id": product_id, "store_id": store_id, "url": f"https://example.com/client-002d-{uuid.uuid4().hex[:8]}"},
        headers=internal_service_headers(),
    )
    assert offer.status_code == 201, offer.text
    offer_id = offer.json()["id"]

    price_resp = client.post(
        "/api/v1/market/prices",
        json={"offer_id": offer_id, "amount": price, "currency": "EUR", "is_real_data": True},
        headers=internal_service_headers(),
    )
    assert price_resp.status_code == 201, price_resp.text

    return product_id, product_name, offer_id


def _ingest_fixture_only_product(client: TestClient, *, price: float):
    """Same shape, but the price is tagged is_real_data=False -- e.g. a
    parked fixture-mode connector (Amazon). Must never appear in the feed."""
    product_name = f"CLIENT-002d Fixture Only {uuid.uuid4().hex[:8]}"
    create = client.post(
        "/api/v1/products/from-name",
        params={"product_name": product_name, "country": "DE"},
        headers=operator_headers(client),
    )
    assert create.status_code == 201, create.text
    product_id = create.json()["id"]

    store = client.post(
        "/api/v1/market/stores",
        json={"name": "CLIENT-002d Fixture Store", "slug": f"client-002d-fx-{uuid.uuid4().hex[:8]}", "country": "DE"},
        headers=internal_service_headers(),
    )
    assert store.status_code == 201, store.text
    store_id = store.json()["id"]

    offer = client.post(
        "/api/v1/market/offers",
        json={"product_id": product_id, "store_id": store_id, "url": f"https://example.com/client-002d-fx-{uuid.uuid4().hex[:8]}"},
        headers=internal_service_headers(),
    )
    assert offer.status_code == 201, offer.text
    offer_id = offer.json()["id"]

    price_resp = client.post(
        "/api/v1/market/prices",
        json={"offer_id": offer_id, "amount": price, "currency": "EUR", "is_real_data": False},
        headers=internal_service_headers(),
    )
    assert price_resp.status_code == 201, price_resp.text

    return product_id, product_name


def test_real_ingested_product_appears_in_deal_feed():
    with TestClient(app) as client:
        product_id, product_name, offer_id = _ingest_real_product(client, price=120.0)

        response = client.post("/api/v1/deal-feed/query", json={"limit": 200})

    assert response.status_code == 200
    body = response.json()
    matches = [item for item in body["items"] if item["canonical_product_key"] and item.get("product_id") == product_id]
    assert matches, f"expected {product_name} ({product_id}) in the feed, got {len(body['items'])} items"
    match = matches[0]
    assert match["offer_id"] == offer_id
    assert match["price"] == 120.0
    assert match["is_real_data"] is True
    assert match["deal_decision"] in ("BUY", "WATCH", "SKIP", None) or isinstance(match["deal_decision"], str)


def test_fixture_only_product_never_appears_in_deal_feed():
    with TestClient(app) as client:
        product_id, product_name = _ingest_fixture_only_product(client, price=1.0)

        response = client.post("/api/v1/deal-feed/query", json={"limit": 500})

    assert response.status_code == 200
    body = response.json()
    leaked = [item for item in body["items"] if item.get("product_id") == product_id]
    assert leaked == [], f"fixture-only product {product_name} leaked into the real deal feed: {leaked}"
    # Also assert no fabricated 1.0-price entry with this product's name anywhere in the payload.
    assert product_name not in str(body)


def test_deal_feed_query_never_crashes_and_returns_honest_shape():
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/deal-feed/query",
            json={"minimum_confidence": 999, "limit": 10},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["items"] == []
    assert body["feed_count"] == 0
