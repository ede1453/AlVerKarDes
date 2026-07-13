from app.domains.price_prediction.price_prediction_engine import PricePredictionEngine


def test_price_prediction_engine_buy_soon_at_history_low():
    result = PricePredictionEngine().predict(
        product_key="macbook-air",
        price_history={
            "latest_price": "949.00",
            "min_price": "949.00",
            "average_price": "999.00",
            "max_price": "1099.00",
            "trend": "DOWN",
            "points": [{"price": "999.00"}, {"price": "949.00"}],
        },
    )

    assert result["recommendation_hint"] == "BUY_SOON"
    assert result["confidence"] >= 80
    assert "CURRENT_AT_HISTORY_LOW" in result["reasons"]


def test_price_prediction_engine_wait_when_trending_down_not_at_low():
    result = PricePredictionEngine().predict(
        product_key="macbook-air",
        price_history={
            "latest_price": "999.00",
            "min_price": "899.00",
            "average_price": "1020.00",
            "max_price": "1099.00",
            "trend": "DOWN",
            "points": [{"price": "1099.00"}, {"price": "999.00"}],
        },
    )

    assert result["direction"] == "DOWN"
    assert result["recommendation_hint"] == "WAIT_OR_WATCH"


def test_price_prediction_engine_insufficient_history():
    result = PricePredictionEngine().predict(product_key="missing", price_history={})

    assert result["confidence"] == 20
    assert result["recommendation_hint"] == "INSUFFICIENT_HISTORY"
