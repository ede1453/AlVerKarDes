from app.domains.products.intelligence.spec_extractor import ProductSpecExtractor


def test_extract_macbook_air_m5_specs():
    spec = ProductSpecExtractor().extract("Apple MacBook Air M5 16GB 512GB Midnight")

    assert spec.brand == "apple"
    assert spec.model_family == "macbook air"
    assert spec.chip == "m5"
    assert spec.ram_gb == 16
    assert spec.storage_gb == 512
    assert spec.color == "midnight"


def test_extract_mba_compact_specs():
    spec = ProductSpecExtractor().extract("Apple MBA M5 16/512 Silver")

    assert spec.model_family == "macbook air"
    assert spec.ram_gb == 16
    assert spec.storage_gb == 512
    assert spec.color == "silver"
