from app.domains.deal_intelligence.service import PriceHistoryAnalyzer


def test_rc145_price_history_analysis():
    result = PriceHistoryAnalyzer().analyze(
        current_price=800,
        historical_prices=[1000, 950, 1050, 900],
    )
    assert result["analyzed"] is True
    assert result["lowest_price"] == 900.0
    assert result["discount_vs_average_pct"] > 10

def test_rc145_no_history():
    result = PriceHistoryAnalyzer().analyze(
        current_price=800,
        historical_prices=[],
    )
    assert result["analyzed"] is False
    assert result["reason"] == "NO_PRICE_HISTORY"
