from app.domains.consumer_trust.service import ConsumerTrustService


def test_rc231_budget_policy():
    result = ConsumerTrustService().evaluate_budget_policy(
        effective_price=700,
        maximum_price=800,
        monthly_budget_remaining=750,
    )
    assert result["eligible"] is True
