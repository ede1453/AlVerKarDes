from app.domains.commerce_ingestion.price_quality import PriceAnomalyDetector


def test_rc140_detect_low_anomaly():
    result = PriceAnomalyDetector().detect(
        current_price=200,
        historical_prices=[900, 1000, 1100],
    )
    assert result["anomalous"] is True
    assert result["reason"] == "UNREALISTICALLY_LOW"

def test_rc140_normal_price():
    result = PriceAnomalyDetector().detect(
        current_price=950,
        historical_prices=[900, 1000, 1100],
    )
    assert result["anomalous"] is False
