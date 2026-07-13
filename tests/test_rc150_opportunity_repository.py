from app.domains.deal_operations.service import OpportunityRepository


def test_rc150_store_and_filter_opportunity():
    repo = OpportunityRepository()
    stored = repo.save_opportunity({
        "source_id":"amazon",
        "canonical_product_key":"apple::macbook-air::m5",
        "price":899,
    })
    assert stored["opportunity_id"]
    assert repo.get_opportunity(
        stored["opportunity_id"]
    )["source_id"] == "amazon"
    assert len(repo.list_opportunities(
        product_key="apple::macbook-air::m5"
    )) == 1
