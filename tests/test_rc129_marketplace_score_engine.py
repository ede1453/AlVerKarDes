from app.domains.commerce_ingestion.marketplace_connectors import MarketplaceScoreEngine


def test_rc129_score_engine():
    result = MarketplaceScoreEngine().calculate(
        current_price=800,
        historical_average_price=1000,
        store_trust_score=90,
        availability="in_stock",
        review_score=4.5,
    )
    assert result["score"] >= 60
    assert result["effective_price"] == 800.0

def test_rc129_invalid_price():
    result = MarketplaceScoreEngine().calculate(
        current_price=0,
        historical_average_price=1000,
        store_trust_score=90,
        availability="in_stock",
    )
    assert result["grade"] == "REJECT"
