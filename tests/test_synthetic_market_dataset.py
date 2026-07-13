from app.domains.market.price_intelligence import PriceHistoryAnalyzer, PricePoint
from app.domains.market.synthetic_dataset import SyntheticMarketDatasetGenerator


def test_synthetic_dataset_counts():
    dataset = SyntheticMarketDatasetGenerator(seed=1).generate(
        product_count=10,
        offers_per_product=3,
        price_points_per_offer=12,
    )

    assert len(dataset.products) == 10
    assert dataset.offer_count == 30
    assert dataset.price_point_count == 360


def test_synthetic_dataset_has_aliases():
    dataset = SyntheticMarketDatasetGenerator(seed=1).generate(product_count=4)

    for product in dataset.products:
        assert product.canonical_name
        assert len(product.aliases) >= 2


def test_synthetic_fake_discount_pattern_detectable():
    dataset = SyntheticMarketDatasetGenerator(seed=1).generate(
        product_count=1,
        offers_per_product=3,
        price_points_per_offer=9,
    )

    fake_discount_offer = dataset.products[0].offers[2]
    points = [
        PricePoint(amount=item.amount, currency=item.currency)
        for item in fake_discount_offer.price_history
    ]

    result = PriceHistoryAnalyzer().analyze(points)

    assert result.fake_discount_risk == "HIGH"
    assert result.signal == "WAIT"
