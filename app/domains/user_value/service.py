from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timedelta, timezone
from statistics import mean, median
from typing import Any
from uuid import uuid4


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def now_iso() -> str:
    return now_utc().isoformat()


class UserValueIntelligenceService:
    def __init__(self) -> None:
        self._savings_events: list[dict[str, Any]] = []
        self._purchase_records: list[dict[str, Any]] = []
        self._watch_entries: dict[str, dict[str, Any]] = {}
        self._journey_events: list[dict[str, Any]] = []

    # RC241 — Savings calculation
    def calculate_savings(
        self,
        *,
        reference_price: float,
        paid_price: float,
        shipping_cost: float = 0,
    ) -> dict[str, Any]:
        effective_paid = float(paid_price) + float(shipping_cost)
        savings = max(float(reference_price) - effective_paid, 0)
        savings_pct = (
            savings / float(reference_price) * 100
            if reference_price > 0
            else 0.0
        )

        return {
            "reference_price": float(reference_price),
            "effective_paid_price": round(effective_paid, 2),
            "savings_amount": round(savings, 2),
            "savings_pct": round(savings_pct, 2),
            "metadata": {
                "version": "user_savings_v1"
            },
        }

    # RC242 — Savings event
    def record_savings_event(
        self,
        *,
        user_id: str,
        deal_id: str,
        reference_price: float,
        paid_price: float,
        shipping_cost: float = 0,
    ) -> dict[str, Any]:
        calculation = self.calculate_savings(
            reference_price=reference_price,
            paid_price=paid_price,
            shipping_cost=shipping_cost,
        )

        event = {
            "savings_event_id": str(uuid4()),
            "user_id": user_id,
            "deal_id": deal_id,
            **calculation,
            "created_at": now_iso(),
        }
        self._savings_events.append(event)

        return {
            "recorded": True,
            "event": deepcopy(event),
        }

    # RC243 — Lifetime savings
    def summarize_lifetime_savings(
        self,
        *,
        user_id: str,
    ) -> dict[str, Any]:
        events = [
            item
            for item in self._savings_events
            if item["user_id"] == user_id
        ]

        return {
            "user_id": user_id,
            "event_count": len(events),
            "total_savings": round(
                sum(
                    item["savings_amount"]
                    for item in events
                ),
                2,
            ),
            "average_savings_pct": round(
                mean(
                    [
                        item["savings_pct"]
                        for item in events
                    ]
                )
                if events
                else 0.0,
                2,
            ),
        }

    # RC244 — Price trend
    def analyze_price_trend(
        self,
        *,
        prices: list[float],
    ) -> dict[str, Any]:
        clean = [float(x) for x in prices]

        if len(clean) < 2:
            return {
                "trend": "INSUFFICIENT_DATA",
                "change_pct": 0.0,
            }

        change = clean[-1] - clean[0]
        change_pct = (
            change / clean[0] * 100
            if clean[0] != 0
            else 0.0
        )

        if change_pct <= -5:
            trend = "FALLING"
        elif change_pct >= 5:
            trend = "RISING"
        else:
            trend = "STABLE"

        return {
            "trend": trend,
            "change_pct": round(change_pct, 2),
            "start_price": clean[0],
            "current_price": clean[-1],
            "minimum_price": min(clean),
            "maximum_price": max(clean),
        }

    # RC245 — Purchase timing
    def evaluate_purchase_timing(
        self,
        *,
        current_price: float,
        historical_prices: list[float],
        trend: str,
        urgency: str = "MEDIUM",
    ) -> dict[str, Any]:
        clean = [float(x) for x in historical_prices]

        if len(clean) < 3:
            return {
                "decision": "WAIT",
                "confidence": 30,
                "reason": "INSUFFICIENT_HISTORY",
            }

        historical_median = median(clean)
        discount_vs_median = (
            (historical_median - current_price)
            / historical_median
            * 100
            if historical_median > 0
            else 0.0
        )

        normalized_urgency = urgency.upper()

        if (
            discount_vs_median >= 20
            and trend != "RISING"
        ):
            decision = "BUY_NOW"
            confidence = 90
        elif (
            discount_vs_median >= 10
            or normalized_urgency == "HIGH"
        ):
            decision = "CONSIDER_BUYING"
            confidence = 70
        else:
            decision = "WAIT"
            confidence = 55

        return {
            "decision": decision,
            "confidence": confidence,
            "discount_vs_median_pct": round(
                discount_vs_median,
                2,
            ),
            "historical_median": round(
                historical_median,
                2,
            ),
        }

    # RC246 — Target price
    def calculate_target_price(
        self,
        *,
        historical_prices: list[float],
        desired_discount_pct: float,
    ) -> dict[str, Any]:
        clean = [float(x) for x in historical_prices]

        if not clean:
            return {
                "calculated": False,
                "reason": "NO_PRICE_HISTORY",
            }

        baseline = median(clean)
        target = baseline * (
            1 - max(desired_discount_pct, 0) / 100
        )

        return {
            "calculated": True,
            "baseline_price": round(baseline, 2),
            "target_price": round(target, 2),
            "desired_discount_pct": float(
                desired_discount_pct
            ),
        }

    # RC247 — Alternative products
    def rank_alternatives(
        self,
        *,
        candidates: list[dict[str, Any]],
        maximum_price: float,
        minimum_confidence: float,
    ) -> dict[str, Any]:
        eligible = []

        for item in candidates:
            price = float(
                item.get(
                    "effective_price",
                    item.get("price", 0),
                )
            )
            confidence = float(
                item.get(
                    "confidence_score",
                    item.get("confidence", 0),
                )
            )

            if price > maximum_price:
                continue

            if confidence < minimum_confidence:
                continue

            score = (
                confidence * 0.7
                + float(
                    item.get(
                        "observed_discount_pct",
                        0,
                    )
                )
                * 0.3
            )

            eligible.append(
                {
                    **item,
                    "alternative_score": round(
                        score,
                        2,
                    ),
                }
            )

        eligible.sort(
            key=lambda x: x[
                "alternative_score"
            ],
            reverse=True,
        )

        return {
            "alternative_count": len(eligible),
            "alternatives": eligible,
            "best_alternative": (
                eligible[0]
                if eligible
                else None
            ),
        }

    # RC248 — Price alert readiness
    def evaluate_price_alert(
        self,
        *,
        current_price: float,
        target_price: float,
        confidence: float,
        minimum_confidence: float = 70,
    ) -> dict[str, Any]:
        triggered = (
            current_price <= target_price
            and confidence >= minimum_confidence
        )

        return {
            "triggered": triggered,
            "current_price": current_price,
            "target_price": target_price,
            "confidence": confidence,
            "reason": (
                "TARGET_REACHED"
                if triggered
                else "TARGET_NOT_REACHED"
            ),
        }

    # RC249 — Watch entry
    def create_watch_entry(
        self,
        *,
        user_id: str,
        product_key: str,
        target_price: float,
        expires_at: str | None = None,
    ) -> dict[str, Any]:
        watch_id = str(uuid4())
        item = {
            "watch_id": watch_id,
            "user_id": user_id,
            "product_key": product_key,
            "target_price": float(target_price),
            "expires_at": expires_at,
            "active": True,
            "created_at": now_iso(),
        }

        self._watch_entries[
            watch_id
        ] = item

        return {
            "created": True,
            "watch": deepcopy(item),
        }

    # RC250 — Watch cleanup
    def expire_watch_entries(
        self,
        *,
        reference_time: str | None = None,
    ) -> dict[str, Any]:
        reference = (
            datetime.fromisoformat(reference_time)
            if reference_time
            else now_utc()
        )

        expired = []

        for item in self._watch_entries.values():
            if (
                item["active"]
                and item["expires_at"]
                and datetime.fromisoformat(
                    item["expires_at"]
                ) <= reference
            ):
                item["active"] = False
                expired.append(item["watch_id"])

        return {
            "expired_count": len(expired),
            "watch_ids": expired,
        }

    # RC251 — Decision explanation
    def explain_decision(
        self,
        *,
        decision: str,
        confidence: float,
        evidence: dict[str, Any],
    ) -> dict[str, Any]:
        reasons = []

        if evidence.get(
            "observed_discount_pct"
        ) is not None:
            reasons.append(
                f"DISCOUNT_{evidence['observed_discount_pct']}"
            )

        if evidence.get(
            "source_confidence"
        ) is not None:
            reasons.append(
                f"SOURCE_{evidence['source_confidence']}"
            )

        if evidence.get(
            "freshness_status"
        ):
            reasons.append(
                f"FRESHNESS_{evidence['freshness_status']}"
            )

        return {
            "decision": decision,
            "confidence": confidence,
            "reasons": reasons,
            "evidence": deepcopy(evidence),
            "explainable": bool(reasons),
        }

    # RC252 — Decision consistency
    def check_decision_consistency(
        self,
        *,
        decision: str,
        confidence: float,
        anomaly_detected: bool,
        source_confidence: float,
    ) -> dict[str, Any]:
        issues = []

        if (
            decision == "BUY"
            and confidence < 70
        ):
            issues.append(
                "BUY_WITH_LOW_CONFIDENCE"
            )

        if (
            decision == "BUY"
            and anomaly_detected
        ):
            issues.append(
                "BUY_WITH_PRICE_ANOMALY"
            )

        if (
            decision == "BUY"
            and source_confidence < 60
        ):
            issues.append(
                "BUY_WITH_LOW_SOURCE_CONFIDENCE"
            )

        return {
            "consistent": len(issues) == 0,
            "issues": issues,
        }

    # RC253 — User journey
    def record_journey_event(
        self,
        *,
        user_id: str,
        event_type: str,
        entity_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        item = {
            "journey_event_id": str(uuid4()),
            "user_id": user_id,
            "event_type": event_type.upper(),
            "entity_id": entity_id,
            "metadata": metadata or {},
            "created_at": now_iso(),
        }

        self._journey_events.append(item)

        return {
            "recorded": True,
            "event": deepcopy(item),
        }

    # RC254 — Funnel metrics
    def calculate_funnel(
        self,
        *,
        user_id: str | None = None,
    ) -> dict[str, Any]:
        items = list(
            self._journey_events
        )

        if user_id is not None:
            items = [
                item
                for item in items
                if item["user_id"] == user_id
            ]

        stages = {
            "VIEWED": 0,
            "SAVED": 0,
            "ALERTED": 0,
            "CLICKED": 0,
            "PURCHASED": 0,
        }

        for item in items:
            if item["event_type"] in stages:
                stages[
                    item["event_type"]
                ] += 1

        return {
            "event_count": len(items),
            "stages": stages,
            "view_to_purchase_rate": (
                round(
                    stages["PURCHASED"]
                    / stages["VIEWED"],
                    4,
                )
                if stages["VIEWED"]
                else 0.0
            ),
        }

    # RC255 — Recommendation value
    def calculate_recommendation_value(
        self,
        *,
        savings_amount: float,
        confidence: float,
        user_relevance_score: float,
        false_positive_risk: float,
    ) -> dict[str, Any]:
        value_score = (
            min(max(savings_amount, 0), 500)
            / 5
            * 0.35
            + min(max(confidence, 0), 100)
            * 0.30
            + min(
                max(user_relevance_score, 0),
                100,
            )
            * 0.25
            + max(
                0,
                100
                - min(
                    max(false_positive_risk, 0),
                    100,
                ),
            )
            * 0.10
        )

        return {
            "value_score": round(
                min(value_score, 100),
                2,
            ),
        }

    # RC256 — Churn risk
    def calculate_churn_risk(
        self,
        *,
        days_since_last_open: int,
        notifications_ignored: int,
        false_positive_reports: int,
        saved_search_count: int,
    ) -> dict[str, Any]:
        risk = (
            min(max(days_since_last_open, 0), 60)
            * 0.8
            + min(
                max(notifications_ignored, 0),
                20,
            )
            * 2
            + min(
                max(false_positive_reports, 0),
                10,
            )
            * 5
            - min(
                max(saved_search_count, 0),
                10,
            )
            * 2
        )

        risk = min(max(risk, 0), 100)

        return {
            "churn_risk_score": round(risk, 2),
            "risk_level": (
                "HIGH"
                if risk >= 70
                else "MEDIUM"
                if risk >= 40
                else "LOW"
            ),
        }

    # RC257 — Retention action
    def recommend_retention_action(
        self,
        *,
        churn_risk_score: float,
        recent_false_positive: bool,
        has_saved_searches: bool,
    ) -> dict[str, Any]:
        if (
            churn_risk_score >= 70
            and recent_false_positive
        ):
            action = "TRUST_RECOVERY_MESSAGE"
        elif (
            churn_risk_score >= 70
            and has_saved_searches
        ):
            action = "HIGH_VALUE_DEAL_DIGEST"
        elif churn_risk_score >= 40:
            action = "PERSONALIZED_REENGAGEMENT"
        else:
            action = "NO_ACTION"

        return {
            "action": action,
            "priority": (
                "HIGH"
                if churn_risk_score >= 70
                else "MEDIUM"
                if churn_risk_score >= 40
                else "LOW"
            ),
        }

    # RC258 — Purchase record
    def record_purchase(
        self,
        *,
        user_id: str,
        deal_id: str,
        product_key: str,
        paid_price: float,
        purchased_at: str | None = None,
    ) -> dict[str, Any]:
        item = {
            "purchase_id": str(uuid4()),
            "user_id": user_id,
            "deal_id": deal_id,
            "product_key": product_key,
            "paid_price": float(paid_price),
            "purchased_at": purchased_at or now_iso(),
        }

        self._purchase_records.append(item)

        return {
            "recorded": True,
            "purchase": deepcopy(item),
        }

    # RC259 — Repeat purchase guard
    def check_repeat_purchase(
        self,
        *,
        user_id: str,
        product_key: str,
        cooldown_days: int,
        reference_time: str | None = None,
    ) -> dict[str, Any]:
        reference = (
            datetime.fromisoformat(reference_time)
            if reference_time
            else now_utc()
        )
        cutoff = reference - timedelta(
            days=max(cooldown_days, 0)
        )

        recent = [
            item
            for item in self._purchase_records
            if item["user_id"] == user_id
            and item["product_key"]
            == product_key
            and datetime.fromisoformat(
                item["purchased_at"]
            ) >= cutoff
        ]

        return {
            "allowed": len(recent) == 0,
            "recent_purchase_count": len(recent),
            "reason": (
                "NO_RECENT_PURCHASE"
                if not recent
                else "RECENT_PURCHASE_EXISTS"
            ),
        }

    # RC260 — User value dashboard
    def build_user_value_dashboard(
        self,
        *,
        user_id: str,
        recommendation_count: int,
        accepted_count: int,
        purchase_count: int,
    ) -> dict[str, Any]:
        savings = self.summarize_lifetime_savings(
            user_id=user_id
        )

        acceptance_rate = (
            accepted_count
            / recommendation_count
            if recommendation_count
            else 0.0
        )

        purchase_rate = (
            purchase_count
            / accepted_count
            if accepted_count
            else 0.0
        )

        return {
            "user_id": user_id,
            "total_savings": savings[
                "total_savings"
            ],
            "average_savings_pct": savings[
                "average_savings_pct"
            ],
            "recommendation_count": recommendation_count,
            "accepted_count": accepted_count,
            "purchase_count": purchase_count,
            "acceptance_rate": round(
                acceptance_rate,
                4,
            ),
            "purchase_rate": round(
                purchase_rate,
                4,
            ),
            "metadata": {
                "version": "user_value_dashboard_v1"
            },
        }
