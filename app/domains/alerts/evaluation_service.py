from decimal import Decimal

from app.domains.alerts.price_alert_engine import PriceAlertEngine, PriceAlertRule


class AlertEvaluationService:
    def __init__(self, rule_repository):
        self.rule_repository = rule_repository
        self.engine = PriceAlertEngine()

    async def evaluate_for_offer(self, *, offer_id, current_price, previous_price=None, price_change=None):
        rules = await self.rule_repository.list_active_for_offer(offer_id)

        results = []

        for rule in rules:
            engine_rule = self._to_engine_rule(rule)
            evaluation = self.engine.evaluate(
                rule=engine_rule,
                current_price=current_price,
                previous_price=previous_price,
                price_change=price_change,
            )

            results.append(
                {
                    "rule_id": str(rule.id),
                    "offer_id": str(rule.offer_id),
                    "rule_type": rule.rule_type,
                    "triggered": evaluation.triggered,
                    "reason": evaluation.reason,
                    "message": evaluation.message,
                }
            )

        return {
            "offer_id": str(offer_id),
            "evaluated_count": len(results),
            "triggered_count": len([item for item in results if item["triggered"]]),
            "results": results,
        }

    def _to_engine_rule(self, rule):
        return PriceAlertRule(
            rule_type=rule.rule_type,
            target_amount=Decimal(str(rule.target_amount)) if rule.target_amount is not None else None,
            drop_percent_threshold=Decimal(str(rule.drop_percent_threshold)) if rule.drop_percent_threshold is not None else None,
            notify_on_back_in_stock=bool(rule.notify_on_back_in_stock),
        )
