"""CONNECT-005 regression test: two different products the identity engine
can't recognize AT ALL (no brand/family/model/memory/storage detected) must
NOT collapse to the same canonical_key. Previously build_canonical_key()
fell back to just the country code (e.g. "de") whenever no identity field
was detected, so ANY two unrecognized products collided and silently
deduped into one products row -- see WIKI_ROOT
07-Issues-Risks/Canonical-Key-Fallback-Veri-Butunlugu-Riski.md.
"""

from app.domains.products.normalization.schemas import ProductNormalizationInput
from app.domains.products.normalization.service import ProductNormalizationService


def normalize(name: str, country: str = "DE"):
    return ProductNormalizationService().normalize(
        ProductNormalizationInput(product_name=name, country=country)
    )


def test_two_different_unrecognized_products_get_different_canonical_keys():
    a = normalize("Regression Test Product 8abd0a40")
    b = normalize("Completely Unknown Item Xyz")

    assert a.canonical_key != b.canonical_key
    assert a.canonical_key != "de"
    assert b.canonical_key != "de"
    assert not a.missing_fields == []  # confirms these genuinely have no detected identity


def test_unrecognized_product_key_is_not_bare_country_code():
    result = normalize("Totally Unbranded Gadget 12345")
    assert result.canonical_key != "de"
    assert result.canonical_key.startswith("unrecognized::")


def test_identical_unrecognized_text_still_dedupes_to_same_key():
    # Same text -> same key is correct dedup behavior, not the bug.
    a = normalize("Completely Unknown Item Xyz")
    b = normalize("Completely Unknown Item Xyz")
    assert a.canonical_key == b.canonical_key


def test_recognized_product_key_format_unchanged():
    # The fix must not alter canonical_key format for products the engine
    # DOES recognize -- brand::family::model::memory::storage::country.
    result = normalize("Apple MacBook Air M3 13 inch 512GB")
    assert result.canonical_key == "apple::macbook-air::m3::512gb::de"


def test_unrecognized_products_from_different_countries_get_different_keys():
    a = normalize("Completely Unknown Item Xyz", country="DE")
    b = normalize("Completely Unknown Item Xyz", country="FR")
    assert a.canonical_key != b.canonical_key
