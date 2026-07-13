from app.domains.marketplace_aggregation.marketplace_aggregator import MarketplaceAggregator


def test_marketplace_aggregator_sorts_offers_by_price():
    result = MarketplaceAggregator().aggregate(
        query="MacBook Air",
        offers=[
            {"marketplace": "amazon", "seller": "Amazon", "product_name": "MacBook Air M3", "price": "999.00", "currency": "EUR"},
            {"marketplace": "saturn", "seller": "Saturn", "product_name": "MacBook Air M3", "price": "949.00", "currency": "EUR"},
        ],
    )

    assert result.offer_count == 2
    assert result.offers[0].marketplace == "saturn"
    assert str(result.min_price) == "949.00"


def test_marketplace_aggregator_filters_by_query_when_possible():
    result = MarketplaceAggregator().aggregate(
        query="iphone",
        offers=[
            {"marketplace": "amazon", "product_name": "MacBook Air", "price": "999.00"},
            {"marketplace": "otto", "product_name": "iPhone 16", "price": "799.00"},
        ],
    )

    assert result.offer_count == 1
    assert result.offers[0].product_name == "iPhone 16"
