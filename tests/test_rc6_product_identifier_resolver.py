from app.domains.products.intelligence.product_identifier_resolver import ProductIdentifierResolver


def test_identifier_resolver_extracts_gtin_from_dict():
    offer = {"gtin": " 04063879000015 "}
    result = ProductIdentifierResolver().resolve(offer)

    assert result.gtin == "04063879000015"
    assert result.strongest_key == "gtin:04063879000015"


def test_identifier_resolver_normalizes_mpn():
    offer = {"mpn": " Apple-MBA-M5 16/512 "}
    result = ProductIdentifierResolver().resolve(offer)

    assert result.mpn == "applembam516512"


def test_identifier_resolver_rejects_invalid_gtin_length():
    offer = {"gtin": "12345", "sku": "SKU 123"}
    result = ProductIdentifierResolver().resolve(offer)

    assert result.gtin is None
    assert result.sku == "sku-123"
    assert result.strongest_key == "sku:sku-123"


def test_identifier_resolver_keys_match_by_gtin():
    left = {"gtin": "04063879000015", "title": "Apple MacBook Air M5"}
    right = {"gtin": "04063879000015", "title": "Apple MBA M5"}

    assert ProductIdentifierResolver().keys_match(left, right) is True


def test_identifier_resolver_keys_do_not_match_when_missing():
    left = {"sku": "A1"}
    right = {"sku": "A1"}

    assert ProductIdentifierResolver().keys_match(left, right) is False
