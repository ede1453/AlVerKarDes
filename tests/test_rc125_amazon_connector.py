from app.domains.commerce_ingestion.marketplace_connectors import AmazonConnector


def test_rc125_amazon_connector():
    result = AmazonConnector().normalize({
        "asin": "B0TEST123",
        "title": "MacBook Air",
        "detail_page_url": "https://amazon.test/item",
        "price": 999,
        "currency": "EUR",
        "availability": "in_stock",
        "merchant_name": "Amazon",
    })
    assert result["marketplace"] == "amazon"
    assert result["external_offer_id"] == "B0TEST123"
    assert result["price"] == 999
