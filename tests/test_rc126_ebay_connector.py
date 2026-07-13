from app.domains.commerce_ingestion.marketplace_connectors import EbayConnector


def test_rc126_ebay_connector():
    result = EbayConnector().normalize({
        "itemId": "ebay-1",
        "title": "Laptop",
        "itemWebUrl": "https://ebay.test/item",
        "price": {"value": "899.99", "currency": "EUR"},
        "seller": {"username": "seller-1"},
    })
    assert result["marketplace"] == "ebay"
    assert result["price"] == "899.99"
    assert result["seller_name"] == "seller-1"
