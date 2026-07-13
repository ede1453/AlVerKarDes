from app.domains.market.price_intelligence import PriceHistoryAnalyzer, PricePoint


def test_price_intelligence_buy_at_historical_low():
    points = [
        PricePoint(1199),
        PricePoint(1099),
        PricePoint(999),
        PricePoint(949),
        PricePoint(899),
        PricePoint(849),
    ]

    result = PriceHistoryAnalyzer().analyze(points)

    assert result.signal == "BUY"
    assert result.current_price == 849
    assert result.historical_lowest == 849
    assert result.position_score >= 85
    assert result.fake_discount_risk == "LOW"
    assert result.confidence >= 60


def test_price_intelligence_wait_when_above_average():
    points = [
        PricePoint(849),
        PricePoint(899),
        PricePoint(949),
        PricePoint(999),
        PricePoint(1099),
        PricePoint(1199),
    ]

    result = PriceHistoryAnalyzer().analyze(points)

    assert result.signal == "WAIT"
    assert result.current_price == 1199
    assert result.position_score <= 5


def test_price_intelligence_insufficient_history():
    points = [
        PricePoint(999),
        PricePoint(949),
    ]

    result = PriceHistoryAnalyzer().analyze(points)

    assert result.signal == "INSUFFICIENT_HISTORY"
    assert result.fake_discount_risk == "UNKNOWN"


def test_price_intelligence_fake_discount_high():
    points = [
        PricePoint(1000),
        PricePoint(1005),
        PricePoint(1500),
        PricePoint(1490),
        PricePoint(1010),
        PricePoint(1000),
    ]

    result = PriceHistoryAnalyzer().analyze(points)

    assert result.fake_discount_risk == "HIGH"
    assert result.signal == "WAIT"
