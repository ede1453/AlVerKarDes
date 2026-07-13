from app.domains.products.matching_engine import ProductMatchEngine


def test_macbook_aliases_match():
    engine = ProductMatchEngine()

    result = engine.compare(
        "Apple MacBook Air M5 16GB 512GB",
        "Apple MBA M5 16/512",
    )

    assert result.same_product is True
    assert result.final_score >= 82
    assert result.confidence_level in {"MEDIUM", "HIGH"}


def test_macbook_parenthetical_alias_matches():
    engine = ProductMatchEngine()

    result = engine.compare(
        "Apple MacBook Air M5 16GB 512GB",
        "MacBook Air M5 (16 GB RAM, 512 GB SSD)",
    )

    assert result.same_product is True
    assert result.final_score >= 82


def test_different_storage_should_not_be_high_confidence_same_product():
    engine = ProductMatchEngine()

    result = engine.compare(
        "Apple MacBook Air M5 16GB 512GB",
        "Apple MacBook Air M5 16GB 256GB",
    )

    assert result.final_score < 95
    assert "storage_mismatch" in result.reasons


def test_different_brand_does_not_match():
    engine = ProductMatchEngine()

    result = engine.compare(
        "Apple MacBook Air M5 16GB 512GB",
        "Lenovo ThinkPad X1 16GB 512GB",
    )

    assert result.same_product is False
    assert result.confidence_level == "LOW"


def test_sony_aliases_match():
    engine = ProductMatchEngine()

    result = engine.compare(
        "Sony WH-1000XM7 Black",
        "WH-1000XM7 Noise Cancelling Headphones",
    )

    assert result.same_product is True
    assert result.final_score >= 82
