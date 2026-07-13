from app.domains.products.normalization.schemas import ProductNormalizationInput
from app.domains.products.normalization.service import ProductNormalizationService


def normalize(name: str):
    return ProductNormalizationService().normalize(
        ProductNormalizationInput(product_name=name, country="DE")
    )


def test_macbook_air_m5_identity_high_confidence():
    result = normalize("Apple MacBook Air M5 16GB 512GB")

    assert result.brand == "Apple"
    assert result.product_family == "Macbook Air"
    assert result.model == "M5"
    assert result.category_hint == "laptop"
    assert result.variant.memory == "16GB"
    assert result.variant.storage == "512GB"
    assert result.confidence >= 90


def test_sony_headphone_identity():
    result = normalize("Sony WH-1000XM7 Black")

    assert result.brand == "Sony"
    assert result.product_family == "WH-1000XM"
    assert result.model == "WH-1000XM7"
    assert result.category_hint == "headphones"
    assert result.confidence >= 70


def test_samsung_galaxy_identity():
    result = normalize("Samsung Galaxy S26 Ultra 512GB")

    assert result.brand == "Samsung"
    assert result.product_family == "Galaxy S"
    assert result.model == "S26"
    assert result.category_hint == "smartphone"
    assert result.variant.storage == "512GB"
    assert result.confidence >= 70
