from app.domains.products.intelligence.product_signature import ProductSignatureBuilder


def test_product_signature_builder_normalizes_equivalent_titles():
    builder = ProductSignatureBuilder()

    left = builder.build("Apple MacBook Air M5 16GB 512GB Midnight")
    right = builder.build("Apple MBA M5 16/512 Silver")

    assert left == right
    assert left == "apple::macbook air::m5::16gb::512gb::de"
