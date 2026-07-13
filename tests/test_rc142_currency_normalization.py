from app.domains.commerce_ingestion.price_quality import CurrencyNormalizer


def test_rc142_currency_conversion():
    result = CurrencyNormalizer().normalize(
        amount=100,
        source_currency="USD",
        target_currency="EUR",
        rates={"USD_EUR":0.92},
    )
    assert result["normalized"] is True
    assert result["amount"] == 92.0
    assert result["currency"] == "EUR"

def test_rc142_missing_rate():
    result = CurrencyNormalizer().normalize(
        amount=100,
        source_currency="USD",
        target_currency="EUR",
        rates={},
    )
    assert result["normalized"] is False
