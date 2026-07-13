from app.domains.deal_lifecycle.service import DealLifecycleService


def test_rc156_decision_versions_supersede():
    service = DealLifecycleService()
    deal = service.register_deal(
        source_id="amazon",
        external_offer_id="offer-1",
        canonical_product_key="product-1",
        observed_at="2026-07-12T10:00:00+00:00",
        price=899,
        currency="EUR",
    )["deal"]
    first = service.append_decision_version(
        deal_id=deal["deal_id"],
        decision="WAIT",
        confidence=55,
        explanation="More data needed",
    )
    second = service.append_decision_version(
        deal_id=deal["deal_id"],
        decision="BUY",
        confidence=85,
        explanation="Strong deal",
    )
    assert first["version"]["version"] == 1
    assert second["version"]["version"] == 2
    assert second["version"]["supersedes_version"] == 1
