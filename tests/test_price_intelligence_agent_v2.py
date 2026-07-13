from app.domains.ai.agents.price_intelligence_agent_v2 import PriceAgentV2Input, PriceIntelligenceAgentV2


def test_price_agent_v2_buy_signal():
    agent = PriceIntelligenceAgentV2()

    output = agent.analyze(
        PriceAgentV2Input(
            prices=[
                {"amount": 1199, "currency": "EUR"},
                {"amount": 1099, "currency": "EUR"},
                {"amount": 999, "currency": "EUR"},
                {"amount": 949, "currency": "EUR"},
                {"amount": 899, "currency": "EUR"},
                {"amount": 849, "currency": "EUR"},
            ]
        )
    )

    assert output.price_signal == "BUY"
    assert output.fake_discount_risk == "LOW"
    assert output.current_price == 849
    assert output.evidence["data"]["position_score"] >= 85


def test_price_agent_v2_fake_discount_wait():
    agent = PriceIntelligenceAgentV2()

    output = agent.analyze(
        PriceAgentV2Input(
            prices=[
                {"amount": 1000, "currency": "EUR"},
                {"amount": 1005, "currency": "EUR"},
                {"amount": 1500, "currency": "EUR"},
                {"amount": 1490, "currency": "EUR"},
                {"amount": 1010, "currency": "EUR"},
                {"amount": 1000, "currency": "EUR"},
            ]
        )
    )

    assert output.price_signal == "WAIT"
    assert output.fake_discount_risk == "HIGH"
    assert output.uncertainty["level"] == "MEDIUM"


def test_price_agent_v2_no_history():
    agent = PriceIntelligenceAgentV2()

    output = agent.analyze(PriceAgentV2Input(prices=[]))

    assert output.price_signal == "INSUFFICIENT_HISTORY"
    assert output.confidence == 0
    assert output.uncertainty["level"] == "HIGH"
