from app.domains.price_history.price_history_engine import PriceHistoryEngine
from app.domains.price_history.price_history_models import create_price_point


def test_price_history_engine_summarizes_down_trend():
    points = [
        create_price_point({"product_key": "macbook-air", "marketplace": "amazon", "price": "999.00"}),
        create_price_point({"product_key": "macbook-air", "marketplace": "saturn", "price": "949.00"}),
    ]

    summary = PriceHistoryEngine().summarize(product_key="macbook-air", points=points)

    assert summary.point_count == 2
    assert str(summary.min_price) == "949.00"
    assert str(summary.max_price) == "999.00"
    assert summary.trend == "DOWN"


def test_price_history_engine_empty_summary():
    summary = PriceHistoryEngine().summarize(product_key="missing", points=[])

    assert summary.point_count == 0
    assert summary.trend == "UNKNOWN"
