from app.domains.products.intelligence.product_match_scorer import ProductMatchScorer


def test_match_scorer_matches_equivalent_macbook_titles():
    result = ProductMatchScorer().score_titles(
        "Apple MacBook Air M5 16GB 512GB Midnight",
        "Apple MBA M5 16/512 Silver",
    )

    assert result.score >= 90
    assert result.decision == "MATCH"
    assert "brand_match" in result.reasons
    assert "model_family_match" in result.reasons
    assert "ram_match" in result.reasons
    assert "storage_match" in result.reasons


def test_match_scorer_detects_different_storage_as_possible_or_no_match():
    result = ProductMatchScorer().score_titles(
        "Apple MacBook Air M5 16GB 512GB",
        "Apple MacBook Air M5 16GB 256GB",
    )

    assert result.score < 90
    assert result.decision in {"POSSIBLE_MATCH", "NO_MATCH"}
    assert "storage_mismatch" in result.reasons


def test_match_scorer_rejects_different_brand():
    result = ProductMatchScorer().score_titles(
        "Apple MacBook Air M5 16GB 512GB",
        "Dell XPS 13 16GB 512GB",
    )

    assert result.decision == "NO_MATCH"
    assert "brand_mismatch" in result.reasons


def test_match_scorer_keeps_match_when_color_only_differs():
    result = ProductMatchScorer().score_titles(
        "Apple MacBook Air M5 16GB 512GB Midnight",
        "Apple MacBook Air M5 16GB 512GB Silver",
    )

    assert result.score >= 90
    assert result.decision == "MATCH"
    assert "color_mismatch" in result.reasons
