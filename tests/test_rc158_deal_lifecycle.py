from app.domains.deal_lifecycle.service import DealLifecycleService


def test_rc158_valid_lifecycle_transition():
    service = DealLifecycleService()
    deal = service.register_deal(
        source_id="amazon",
        external_offer_id="offer-1",
        canonical_product_key="product-1",
        observed_at="2026-07-12T10:00:00+00:00",
        price=899,
        currency="EUR",
    )["deal"]
    result = service.transition_status(
        deal_id=deal["deal_id"],
        new_status="VALIDATED",
        reason="Checks passed",
    )
    assert result["transitioned"] is True
    assert result["deal"]["status"] == "VALIDATED"

def test_rc158_invalid_transition_rejected():
    service = DealLifecycleService()
    deal = service.register_deal(
        source_id="amazon",
        external_offer_id="offer-1",
        canonical_product_key="product-1",
        observed_at="2026-07-12T10:00:00+00:00",
        price=899,
        currency="EUR",
    )["deal"]
    result = service.transition_status(
        deal_id=deal["deal_id"],
        new_status="ALERTED",
        reason="Invalid jump",
    )
    assert result["transitioned"] is False
    assert result["reason"] == "INVALID_STATUS_TRANSITION"
