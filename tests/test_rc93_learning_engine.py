from decimal import Decimal

from app.domains.decision_memory.learning_engine import DecisionLearningEngine


def test_learning_engine_marks_buy_now_correct_when_price_increases():
    result = DecisionLearningEngine().evaluate_outcome(
        final_decision="BUY_NOW",
        decision_price=Decimal("100.00"),
        future_price=Decimal("120.00"),
    )

    assert result["decision_correct"] is True
    assert result["learning_signal"] == "POSITIVE"


def test_learning_engine_marks_buy_now_wrong_when_price_drops():
    result = DecisionLearningEngine().evaluate_outcome(
        final_decision="BUY_NOW",
        decision_price=Decimal("100.00"),
        future_price=Decimal("90.00"),
    )

    assert result["decision_correct"] is False
    assert result["learning_signal"] == "NEGATIVE"
