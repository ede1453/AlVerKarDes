from app.domains.deal_lifecycle.service import DealLifecycleService


def test_rc159_queries_and_events():
    service = DealLifecycleService()
    deal = service.register_deal(
        source_id="amazon",
        external_offer_id="offer-1",
        canonical_product_key="product-1",
        observed_at="2026-07-12T10:00:00+00:00",
        price=899,
        currency="EUR",
    )["deal"]
    service.transition_status(
        deal_id=deal["deal_id"],
        new_status="VALIDATED",
        reason="Checks passed",
    )
    deals = service.list_deals(status="VALIDATED")
    events = service.list_events(deal_id=deal["deal_id"])
    assert deals["deal_count"] == 1
    assert events["event_count"] == 2
