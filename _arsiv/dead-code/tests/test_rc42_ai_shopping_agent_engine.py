from app.domains.ai_shopping_agent.agent_engine import AIShoppingAgentEngine


def test_ai_shopping_agent_engine_buy_now_with_strong_signals():
    result = AIShoppingAgentEngine().decide(
        query="MacBook Air",
        user_id="user-1",
        search={"status": "FOUND", "top_offer": {"marketplace": "saturn"}},
        matching={"group_count": 1},
        price_history={"trend": "DOWN"},
        personalization={"top_offer": {"marketplace": "saturn", "personalization_score": 95}},
    )

    assert result["decision"] == "BUY_NOW"
    assert result["confidence"] >= 80
    assert "HIGH_PERSONALIZATION_SCORE" in result["reasons"]


def test_ai_shopping_agent_engine_wait_with_weak_signals():
    result = AIShoppingAgentEngine().decide(
        query="Unknown",
        user_id=None,
        search={"status": "NO_RESULTS", "top_offer": None},
        matching={"group_count": 0},
        price_history={"trend": "UP"},
        personalization=None,
    )

    assert result["decision"] == "WAIT"
