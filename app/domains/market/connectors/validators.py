from urllib.parse import urlparse

VALID_CURRENCIES = {"EUR", "USD", "TRY", "GBP"}


def validate_feed_item(item) -> list[str]:
    errors = []
    if not item.store_slug:
        errors.append("missing_store_slug")
    if not item.product_title or len(item.product_title) < 3:
        errors.append("invalid_product_title")
    if item.price <= 0:
        errors.append("invalid_price")
    parsed = urlparse(item.product_url)
    if not parsed.scheme or not parsed.netloc:
        errors.append("invalid_url")
    if item.currency not in VALID_CURRENCIES:
        errors.append("invalid_currency")
    return errors
