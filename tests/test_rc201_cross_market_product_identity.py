from app.domains.deal_feed.service import ProductIdentityResolver


def test_rc201_existing_canonical_key():
    result = ProductIdentityResolver().resolve(
        offer={
            "canonical_product_key":"apple::macbook-air::m5"
        }
    )
    assert result["resolved"] is True
    assert result["confidence"] == 100

def test_rc201_build_identity_from_fields():
    result = ProductIdentityResolver().resolve(
        offer={
            "brand":"Apple",
            "product_family":"MacBook Air",
            "model":"M5",
            "memory":"16GB",
            "storage":"512GB",
        }
    )
    assert result["resolved"] is True
    assert result["product_key"] == "apple::macbook-air::m5::16gb::512gb"
