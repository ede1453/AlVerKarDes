from app.domains.product_matching.product_matching_engine import ProductMatchingEngine


def test_product_matching_engine_groups_similar_offers():
    result = ProductMatchingEngine().match(
        query="MacBook Air",
        offers=[
            {"id": "1", "marketplace": "amazon", "product_name": "MacBook Air M3 13", "price": "999.00"},
            {"id": "2", "marketplace": "saturn", "product_name": "MacBook Air M3 13", "price": "949.00"},
            {"id": "3", "marketplace": "otto", "product_name": "iPhone 16", "price": "799.00"},
        ],
    )

    assert result.group_count == 2
    assert result.groups[0].match_confidence == 88
    assert len(result.groups[0].candidates) == 2


def test_product_matching_engine_single_offer_confidence_is_lower():
    result = ProductMatchingEngine().match(
        query="iPhone",
        offers=[
            {"id": "1", "marketplace": "otto", "product_name": "iPhone 16", "price": "799.00"},
        ],
    )

    assert result.group_count == 1
    assert result.groups[0].match_confidence == 70
