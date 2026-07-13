from app.domains.deal_feed.service import OfferDeduplicator


def test_rc202_duplicate_offer_removed():
    offer = {
        "source_id":"amazon",
        "external_offer_id":"A1",
        "canonical_product_key":"product-1",
        "price":700,
        "currency":"EUR",
    }
    result = OfferDeduplicator().deduplicate(
        offers=[offer, dict(offer)]
    )
    assert result["input_count"] == 2
    assert result["unique_count"] == 1
    assert result["duplicate_count"] == 1
