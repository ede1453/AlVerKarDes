from app.domains.products.intelligence.merge_candidate_service import MergeCandidateService


def test_merge_candidate_service_returns_candidates():
    result = MergeCandidateService().build_from_offers(
        country="DE",
        offers=[
            {"source": "amazon-de", "title": "Apple MacBook Air M5 16GB 512GB Midnight"},
            {"source": "mediamarkt-de", "title": "Apple MBA M5 16/512 Silver"},
        ],
    )

    assert result["country"] == "DE"
    assert result["input_offer_count"] == 2
    assert result["candidate_count"] == 1
    assert result["candidates"][0]["decision"] == "AUTO_MERGE"
