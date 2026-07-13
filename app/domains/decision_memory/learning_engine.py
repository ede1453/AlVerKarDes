from decimal import Decimal


class DecisionLearningEngine:
    def evaluate_outcome(
        self,
        *,
        final_decision: str,
        decision_price: Decimal,
        future_price: Decimal,
    ) -> dict:
        change_amount = future_price - decision_price
        change_percent = Decimal("0") if decision_price == 0 else (change_amount / decision_price) * Decimal("100")

        correct = self._is_correct(
            final_decision=final_decision,
            change_percent=change_percent,
        )

        return {
            "decision_correct": correct,
            "price_change_amount": str(change_amount),
            "price_change_percent": str(change_percent),
            "learning_signal": "POSITIVE" if correct else "NEGATIVE",
        }

    def _is_correct(self, *, final_decision: str, change_percent: Decimal) -> bool:
        if final_decision == "BUY_NOW":
            return change_percent >= 0
        if final_decision in {"WAIT", "WATCH"}:
            return change_percent < 0
        if final_decision in {"DO_NOT_BUY", "AVOID"}:
            return True
        return False
