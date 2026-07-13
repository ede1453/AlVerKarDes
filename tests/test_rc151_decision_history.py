from app.domains.deal_operations.service import OpportunityRepository


def test_rc151_decision_history():
    repo = OpportunityRepository()
    opportunity = repo.save_opportunity({
        "source_id":"amazon",
        "canonical_product_key":"product-1",
        "price":899,
    })
    repo.append_decision(
        opportunity_id=opportunity["opportunity_id"],
        decision={
            "decision":"BUY",
            "confidence":85,
        },
    )
    history = repo.get_decision_history(
        opportunity["opportunity_id"]
    )
    assert len(history) == 1
    assert history[0]["decision"]["decision"] == "BUY"
