from app.domains.consumer_trust.service import ConsumerTrustService


def test_rc233_saved_search():
    service = ConsumerTrustService()
    service.create_saved_search(
        user_id="u1",
        name="MacBook deals",
        filters={"brand":"Apple"},
    )
    result = service.list_saved_searches(
        user_id="u1"
    )
    assert result["search_count"] == 1
