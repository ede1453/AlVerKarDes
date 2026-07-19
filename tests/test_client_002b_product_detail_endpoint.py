"""CLIENT-002b (ADR-011): GET /products/{id}/detail -- a single PUBLIC
aggregator endpoint for the Next.js SSR product page. Combines three
already-real data sources (offers, price-history summary, deal signal)
without re-implementing any of them a second time:
  - MarketService.get_offers_with_latest_price_for_product (same as
    GET /market/products/{id}/offers, CLIENT-000b)
  - MarketService.get_price_history_summary_for_product (new, but its
    math is a straight extraction of shopping_pipeline_service's
    CONNECT-001 logic -- covered here AND indirectly re-verified by the
    existing CONNECT-001/CLIENT-000b pipeline tests, which must still pass
    unchanged after the refactor)
  - OfferDealSummaryService.summarize_offer (same as
    GET /deals/offers/{offer_id}/summary)

All setup goes through real HTTP endpoints on the same TestClient (not a
second AsyncSessionLocal()/engine mixed into the same test) -- this
codebase's Windows+asyncpg TestClient portal hits "attached to a different
loop" if a raw async session is opened in the same test as a TestClient
call (see tests/conftest.py's dispose_db_engine_after_test and
tests/auth_test_helpers.py's _promote_role comment for the same failure
mode elsewhere).
"""

import uuid

from fastapi.testclient import TestClient

from app.main import app
from tests.auth_test_helpers import internal_service_headers, operator_headers


def _ingest_product_with_prices(client: TestClient, *, prices: list[float]):
    product_name = f"CLIENT-002b Test Product {uuid.uuid4().hex[:8]}"

    create = client.post(
        "/api/v1/products/from-name",
        params={"product_name": product_name, "country": "DE"},
        headers=operator_headers(client),
    )
    assert create.status_code == 201, create.text
    product_id = create.json()["id"]
    canonical_key = create.json()["canonical_key"]

    store = client.post(
        "/api/v1/market/stores",
        json={"name": "CLIENT-002b Test Store", "slug": f"client-002b-{uuid.uuid4().hex[:8]}", "country": "DE"},
        headers=internal_service_headers(),
    )
    assert store.status_code == 201, store.text
    store_id = store.json()["id"]

    offer = client.post(
        "/api/v1/market/offers",
        json={"product_id": product_id, "store_id": store_id, "url": f"https://example.com/client-002b-{uuid.uuid4().hex[:8]}"},
        headers=internal_service_headers(),
    )
    assert offer.status_code == 201, offer.text
    offer_id = offer.json()["id"]

    for amount in prices:
        price = client.post(
            "/api/v1/market/prices",
            json={"offer_id": offer_id, "amount": amount, "currency": "EUR", "is_real_data": True},
            headers=internal_service_headers(),
        )
        assert price.status_code == 201, price.text

    return product_id, canonical_key, offer_id


def test_detail_endpoint_returns_real_offers_price_history_and_deal_signal():
    with TestClient(app) as client:
        product_id, canonical_key, offer_id = _ingest_product_with_prices(client, prices=[100.00, 80.00])

        response = client.get(f"/api/v1/products/{product_id}/detail")

    assert response.status_code == 200
    body = response.json()

    assert body["product"]["id"] == product_id
    assert body["product"]["canonical_key"] == canonical_key

    assert len(body["offers"]) == 1
    assert body["offers"][0]["store"] == "CLIENT-002b Test Store"
    assert body["offers"][0]["price"] == 80.00
    assert body["offers"][0]["is_real_data"] is True

    assert body["price_history"]["status"] == "OK"
    assert body["price_history"]["latest_price"] == "80.00"
    assert body["price_history"]["min_price"] == "80.00"
    assert body["price_history"]["max_price"] == "100.00"
    assert body["price_history"]["trend"] == "DOWN"

    assert body["deal_signal"] is not None
    assert body["deal_signal"]["offer_id"] == offer_id
    assert body["deal_signal"]["has_price_data"] is True


def test_detail_endpoint_handles_ingested_product_with_no_offers():
    product_name = f"CLIENT-002b No Offers {uuid.uuid4().hex[:8]}"

    with TestClient(app) as client:
        create = client.post(
            "/api/v1/products/from-name",
            params={"product_name": product_name, "country": "DE"},
            headers=operator_headers(client),
        )
        assert create.status_code == 201, create.text
        product_id = create.json()["id"]

        response = client.get(f"/api/v1/products/{product_id}/detail")

    assert response.status_code == 200
    body = response.json()
    assert body["offers"] == []
    assert body["price_history"]["status"] == "INSUFFICIENT_DATA"
    assert body["deal_signal"] is None
    # No fabricated data anywhere in the empty-state response.
    assert "949.00" not in str(body)


def test_detail_endpoint_returns_404_for_unknown_product_id():
    with TestClient(app) as client:
        response = client.get(f"/api/v1/products/{uuid.uuid4()}/detail")

    assert response.status_code == 404
    assert response.json()["detail"] == "product_not_found"


def test_detail_endpoint_rejects_malformed_product_id():
    with TestClient(app) as client:
        response = client.get("/api/v1/products/not-a-uuid/detail")

    assert response.status_code == 422
