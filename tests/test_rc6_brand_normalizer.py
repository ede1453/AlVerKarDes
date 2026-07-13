from app.domains.products.intelligence.brand_normalizer import BrandNormalizer


def test_brand_normalizer_lowercases_and_cleans():
    assert BrandNormalizer().normalize(" APPLE™ ") == "apple"


def test_brand_normalizer_aliases_apple_inc():
    assert BrandNormalizer().normalize("Apple Inc.") == "apple"


def test_brand_normalizer_returns_none_for_missing():
    assert BrandNormalizer().normalize(None) is None
