from app.domains.decision.contract import DecisionContract, DecisionSignal


def test_decision_contract():
    decision = DecisionContract(
        decision="BUY",
        confidence=82,
        positive_signals=[
            DecisionSignal(
                type="PRICE",
                title="Strong price",
                description="Current price is near historical low.",
                weight=0.8,
                confidence=88,
            )
        ],
        what_could_change_my_decision=["A lower price from a trusted store."],
        uncertainty={"level": "LOW"},
        affiliate_disclosure={"contains_affiliate_links": False},
    )

    assert decision.decision == "BUY"
    assert decision.confidence == 82
