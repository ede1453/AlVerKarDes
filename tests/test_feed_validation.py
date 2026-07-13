from app.domains.market.connectors.validators import validate_feed_item


class Dummy:
    def __init__(self):
        self.store_slug = "amazon-de"
        self.product_title = "MacBook Air M5"
        self.product_url = "https://amazon.de/product"
        self.price = 1000
        self.currency = "EUR"


def test_valid_feed():
    assert validate_feed_item(Dummy()) == []


def test_invalid_price():
    item = Dummy()
    item.price = -5
    assert "invalid_price" in validate_feed_item(item)
