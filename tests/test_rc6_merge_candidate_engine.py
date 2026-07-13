from app.domains.products.intelligence.cross_store_resolver import CrossStoreProductResolver
from app.domains.products.intelligence.merge_candidate_engine import MergeCandidateEngine


def test_merge_candidate_engine_creates_auto_merge_candidate():
    offers = [
        {"source": "amazon-de", "title": "Apple MacBook Air M5 16GB 512GB Midnight"},
        {"source": "mediamarkt-de", "title": "Apple MBA M5 16/512 Silver"},
    ]

    groups = CrossStoreProductResolver().resolve(offers)
    candidates = MergeCandidateEngine().build_candidates(groups)

    assert len(candidates) == 1
    assert candidates[0].decision == "AUTO_MERGE"
    assert candidates[0].offer_count == 2
    assert candidates[0].average_confidence >= 90
    assert "amazon-de" in candidates[0].sources
    assert "mediamarkt-de" in candidates[0].sources


def test_merge_candidate_engine_skips_single_offer_groups():
    offers = [
        {"source": "amazon-de", "title": "Apple MacBook Air M5 16GB 512GB"},
        {"source": "dell-de", "title": "Dell XPS 13 16GB 512GB"},
    ]

    groups = CrossStoreProductResolver().resolve(offers)
    candidates = MergeCandidateEngine().build_candidates(groups)

    assert candidates == []


def test_merge_candidate_engine_marks_review_for_lower_confidence_group():
    class Group:
        signature = "test::signature"
        master_title = "Test Product"
        offers = [
            {"source": "a", "title": "A"},
            {"source": "b", "title": "B"},
        ]
        offer_count = 2
        average_confidence = 75.0

    candidates = MergeCandidateEngine().build_candidates([Group()])

    assert len(candidates) == 1
    assert candidates[0].decision == "REVIEW"


def test_merge_candidate_engine_marks_do_not_merge_for_low_confidence_group():
    class Group:
        signature = "test::signature"
        master_title = "Test Product"
        offers = [
            {"source": "a", "title": "A"},
            {"source": "b", "title": "B"},
        ]
        offer_count = 2
        average_confidence = 40.0

    candidates = MergeCandidateEngine().build_candidates([Group()])

    assert len(candidates) == 1
    assert candidates[0].decision == "DO_NOT_MERGE"
