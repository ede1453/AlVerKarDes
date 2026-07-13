from dataclasses import dataclass
from decimal import Decimal

LEGACY_REASON_MAP = {
    "drop_percent_threshold_reached": "drop_percent_reached",
    "drop_percent_threshold_not_reached": "price_not_down",
    "back_in_stock_detected": "back_in_stock",
}


@dataclass
class PriceAlertRule:
    rule_type: str
    target_amount: Decimal | None = None
    drop_percent_threshold: Decimal | None = None
    notify_on_back_in_stock: bool = False
    is_active: bool = True


@dataclass
class PriceAlertContext:
    current_amount: Decimal
    previous_amount: Decimal | None = None
    target_amount: Decimal | None = None
    drop_percent_threshold: Decimal | None = None
    previous_lowest_amount: Decimal | None = None
    current_stock_status: str | None = None
    previous_stock_status: str | None = None
    price_change_direction: str | None = None
    price_change_percent: Decimal | None = None


@dataclass
class PriceAlertDecision:
    should_notify: bool
    alert_type: str | None
    reasons: list[str]
    data: dict

    @property
    def triggered(self) -> bool:
        return self.should_notify

    @property
    def reason(self) -> str:
        value = self.reasons[0] if self.reasons else ""
        return LEGACY_REASON_MAP.get(value, value)

    @property
    def message(self) -> str:
        if self.should_notify:
            if self.alert_type == "TARGET_PRICE":
                return "Target price reached."
            if self.alert_type == "DROP_PERCENT":
                return "Price drop threshold reached."
            if self.alert_type == "NEW_LOWEST_PRICE":
                return "New lowest price detected."
            if self.alert_type == "BACK_IN_STOCK":
                return "Product is back in stock."
            return "Alert triggered."

        if self.alert_type == "TARGET_PRICE":
            return "Target price not reached."
        if self.alert_type == "DROP_PERCENT":
            return "Price drop threshold not reached."
        if self.alert_type == "NEW_LOWEST_PRICE":
            return "No new lowest price detected."
        if self.alert_type == "BACK_IN_STOCK":
            return "Product is not back in stock."
        return "Alert not triggered."


class PriceAlertEngine:
    def evaluate(self, *args, **kwargs):
        if args and isinstance(args[0], PriceAlertContext):
            return self.evaluate_context(args[0])

        rule = None

        if args and isinstance(args[0], PriceAlertRule):
            rule = args[0]

        if rule is None and isinstance(kwargs.get("rule"), PriceAlertRule):
            rule = kwargs["rule"]

        if rule is not None:
            context = kwargs.get("context") or self._context_from_legacy_kwargs(rule, kwargs)
            return self.evaluate_rule(rule, context)

        raise TypeError("evaluate expects PriceAlertContext or PriceAlertRule")

    def evaluate_context(self, context: PriceAlertContext) -> list[PriceAlertDecision]:
        decisions = [
            self._target_price_alert(context),
            self._drop_percent_alert(context),
            self._new_lowest_price_alert(context),
            self._back_in_stock_alert(context),
        ]
        return [decision for decision in decisions if decision.should_notify]

    def evaluate_rule(self, rule: PriceAlertRule, context: PriceAlertContext) -> PriceAlertDecision:
        if not rule.is_active:
            return self._no(rule.rule_type, "rule_inactive")

        rule_type = rule.rule_type.upper().strip()

        rule_context = PriceAlertContext(
            current_amount=context.current_amount,
            previous_amount=context.previous_amount,
            target_amount=rule.target_amount if rule.target_amount is not None else context.target_amount,
            drop_percent_threshold=(
                rule.drop_percent_threshold
                if rule.drop_percent_threshold is not None
                else context.drop_percent_threshold
            ),
            previous_lowest_amount=context.previous_lowest_amount,
            current_stock_status=context.current_stock_status,
            previous_stock_status=context.previous_stock_status,
            price_change_direction=context.price_change_direction,
            price_change_percent=context.price_change_percent,
        )

        if rule_type == "TARGET_PRICE":
            return self._target_price_alert(rule_context)

        if rule_type == "DROP_PERCENT":
            return self._drop_percent_alert(rule_context)

        if rule_type == "NEW_LOWEST_PRICE":
            return self._new_lowest_price_alert(rule_context)

        if rule_type == "BACK_IN_STOCK":
            if not rule.notify_on_back_in_stock:
                return self._no("BACK_IN_STOCK", "back_in_stock_notification_disabled")
            return self._back_in_stock_alert(rule_context)

        return self._no(rule_type, "unsupported_rule_type")

    def _context_from_legacy_kwargs(self, rule: PriceAlertRule, kwargs: dict) -> PriceAlertContext:
        current_price = kwargs.get("current_price")
        previous_price = kwargs.get("previous_price")
        price_change = kwargs.get("price_change")

        current_amount = self._extract_amount(current_price)
        if current_amount is None:
            current_amount = self._optional_decimal(kwargs.get("current_amount")) or Decimal("0")

        previous_amount = self._extract_amount(previous_price)
        if previous_amount is None:
            previous_amount = self._optional_decimal(kwargs.get("previous_amount"))

        current_stock_status = self._extract_stock_status(current_price)
        if current_stock_status is None:
            current_stock_status = kwargs.get("current_stock_status")

        previous_stock_status = self._extract_stock_status(previous_price)
        if previous_stock_status is None:
            previous_stock_status = kwargs.get("previous_stock_status")

        direction = getattr(price_change, "direction", None) if price_change is not None else None
        change_percent = getattr(price_change, "change_percent", None) if price_change is not None else None

        return PriceAlertContext(
            current_amount=current_amount,
            previous_amount=previous_amount,
            target_amount=rule.target_amount,
            drop_percent_threshold=rule.drop_percent_threshold,
            previous_lowest_amount=self._optional_decimal(kwargs.get("previous_lowest_amount")),
            current_stock_status=current_stock_status,
            previous_stock_status=previous_stock_status,
            price_change_direction=direction,
            price_change_percent=self._optional_decimal(change_percent),
        )

    def _target_price_alert(self, context: PriceAlertContext) -> PriceAlertDecision:
        if context.target_amount is None:
            return self._no("TARGET_PRICE", "target_amount_missing")

        if context.current_amount <= context.target_amount:
            return PriceAlertDecision(
                should_notify=True,
                alert_type="TARGET_PRICE",
                reasons=["target_price_reached"],
                data={
                    "current_amount": str(context.current_amount),
                    "target_amount": str(context.target_amount),
                },
            )

        return self._no("TARGET_PRICE", "target_price_not_reached")

    def _drop_percent_alert(self, context: PriceAlertContext) -> PriceAlertDecision:
        if context.drop_percent_threshold is None:
            return self._no("DROP_PERCENT", "drop_percent_input_missing")

        if context.price_change_percent is not None:
            direction = (context.price_change_direction or "").upper()
            drop_percent = abs(context.price_change_percent)

            if direction == "DOWN" and drop_percent >= context.drop_percent_threshold:
                return PriceAlertDecision(
                    should_notify=True,
                    alert_type="DROP_PERCENT",
                    reasons=["drop_percent_threshold_reached"],
                    data={
                        "current_amount": str(context.current_amount),
                        "drop_percent": str(drop_percent.quantize(Decimal("0.01"))),
                        "threshold": str(context.drop_percent_threshold),
                    },
                )

            return self._no("DROP_PERCENT", "drop_percent_threshold_not_reached")

        if context.previous_amount is None:
            return self._no("DROP_PERCENT", "drop_percent_input_missing")

        if context.previous_amount <= 0:
            return self._no("DROP_PERCENT", "previous_amount_invalid")

        drop_percent = ((context.previous_amount - context.current_amount) / context.previous_amount) * Decimal("100")

        if drop_percent >= context.drop_percent_threshold:
            return PriceAlertDecision(
                should_notify=True,
                alert_type="DROP_PERCENT",
                reasons=["drop_percent_threshold_reached"],
                data={
                    "previous_amount": str(context.previous_amount),
                    "current_amount": str(context.current_amount),
                    "drop_percent": str(drop_percent.quantize(Decimal("0.01"))),
                    "threshold": str(context.drop_percent_threshold),
                },
            )

        return self._no("DROP_PERCENT", "drop_percent_threshold_not_reached")

    def _new_lowest_price_alert(self, context: PriceAlertContext) -> PriceAlertDecision:
        if context.previous_lowest_amount is None:
            return self._no("NEW_LOWEST_PRICE", "previous_lowest_amount_missing")

        if context.current_amount < context.previous_lowest_amount:
            return PriceAlertDecision(
                should_notify=True,
                alert_type="NEW_LOWEST_PRICE",
                reasons=["new_lowest_price_detected"],
                data={
                    "current_amount": str(context.current_amount),
                    "previous_lowest_amount": str(context.previous_lowest_amount),
                },
            )

        return self._no("NEW_LOWEST_PRICE", "not_new_lowest_price")

    def _back_in_stock_alert(self, context: PriceAlertContext) -> PriceAlertDecision:
        previous = (context.previous_stock_status or "").lower()
        current = (context.current_stock_status or "").lower()

        was_out = previous in {"out_of_stock", "sold_out", "unavailable"}
        is_in = current in {"in_stock", "available"}

        if was_out and is_in:
            return PriceAlertDecision(
                should_notify=True,
                alert_type="BACK_IN_STOCK",
                reasons=["back_in_stock_detected"],
                data={
                    "previous_stock_status": context.previous_stock_status,
                    "current_stock_status": context.current_stock_status,
                },
            )

        return self._no("BACK_IN_STOCK", "not_back_in_stock")

    def _no(self, alert_type: str, reason: str) -> PriceAlertDecision:
        return PriceAlertDecision(
            should_notify=False,
            alert_type=alert_type,
            reasons=[reason],
            data={},
        )

    def _extract_amount(self, price):
        if price is None:
            return None
        if isinstance(price, dict):
            value = price.get("amount") or price.get("price")
        else:
            value = getattr(price, "amount", None)
            if value is None:
                value = getattr(price, "price", None)
        return self._optional_decimal(value)

    def _extract_stock_status(self, price):
        if price is None:
            return None
        if isinstance(price, dict):
            return price.get("stock_status")
        return getattr(price, "stock_status", None)

    def _optional_decimal(self, value):
        if value is None:
            return None
        return Decimal(str(value))
