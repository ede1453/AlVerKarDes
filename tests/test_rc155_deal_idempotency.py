from app.domains.deal_lifecycle.service import DealLifecycleService


def test_rc155_duplicate_deal_rejected():
    service = DealLifecycleService()
    payload = dict(
        source_id="amazon",
        external_offer_id="offer-1",
        canonical_product_key="product-1",
        observed_at="2026-07-12T10:00:00+00:00",
        price=899,
        currency="EUR",
    )
    first = service.register_deal(**payload)
    second = service.register_deal(**payload)
    assert first["registered"] is True
    assert second["registered"] is False
    assert second["reason"] == "DUPLICATE_DEAL"
