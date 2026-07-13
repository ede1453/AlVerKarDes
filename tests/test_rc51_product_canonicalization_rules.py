from app.domains.product_canonicalization.canonical_rules import ProductCanonicalRules


def test_canonical_rules_detect_brand_model_variant_category():
    rules = ProductCanonicalRules()
    normalized = rules.normalize("Apple MacBook Air M3 13 inch 512GB")

    assert rules.detect_brand(normalized) == "apple"
    assert rules.detect_model(normalized) == "macbook air m3"
    assert "512GB".lower() in rules.detect_variant(normalized).lower()
    assert rules.infer_category(normalized) == "laptop"


def test_canonical_rules_builds_key():
    rules = ProductCanonicalRules()
    key = rules.canonical_key(
        brand="apple",
        model="macbook air m3",
        variant="512gb-13inch",
        fallback="Apple MacBook Air M3",
    )

    assert key == "apple-macbook-air-m3-512gb-13inch"
