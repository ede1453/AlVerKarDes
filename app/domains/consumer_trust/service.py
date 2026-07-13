from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def now_iso() -> str:
    return now_utc().isoformat()


class ConsumerTrustService:
    def __init__(self) -> None:
        self._delivery_log: list[dict[str, Any]] = []
        self._provider_health: dict[str, dict[str, Any]] = {}
        self._feedback: list[dict[str, Any]] = []
        self._trust_scores: dict[str, dict[str, Any]] = {}
        self._saved_searches: dict[str, dict[str, Any]] = {}
        self._purchase_intents: dict[str, dict[str, Any]] = {}
        self._conversions: list[dict[str, Any]] = []
        self._recommendation_audits: list[dict[str, Any]] = []

    # RC221 — Notification fatigue score
    def calculate_notification_fatigue(
        self,
        *,
        delivered_count_24h: int,
        opened_count_24h: int,
        dismissed_count_24h: int,
        duplicate_count_24h: int,
    ) -> dict[str, Any]:
        delivered = max(delivered_count_24h, 0)
        opened = max(opened_count_24h, 0)
        dismissed = max(dismissed_count_24h, 0)
        duplicates = max(duplicate_count_24h, 0)

        open_rate = opened / delivered if delivered else 0.0
        score = min(
            100.0,
            delivered * 4
            + dismissed * 8
            + duplicates * 12
            + (1 - open_rate) * 30,
        )

        if score >= 75:
            level = "HIGH"
        elif score >= 45:
            level = "MEDIUM"
        else:
            level = "LOW"

        return {
            "fatigue_score": round(score, 2),
            "fatigue_level": level,
            "open_rate": round(open_rate, 4),
            "metadata": {
                "version": "notification_fatigue_v1"
            },
        }

    # RC222 — Frequency cap
    def evaluate_frequency_cap(
        self,
        *,
        user_id: str,
        channel: str,
        max_deliveries: int,
        window_hours: int,
        reference_time: str | None = None,
    ) -> dict[str, Any]:
        reference = (
            datetime.fromisoformat(reference_time)
            if reference_time
            else now_utc()
        )
        cutoff = reference - timedelta(
            hours=max(window_hours, 0)
        )

        count = sum(
            1
            for item in self._delivery_log
            if item["user_id"] == user_id
            and item["channel"] == channel.lower()
            and datetime.fromisoformat(
                item["delivered_at"]
            ) >= cutoff
        )

        return {
            "allowed": count < max_deliveries,
            "current_count": count,
            "maximum_count": max_deliveries,
            "remaining_count": max(
                max_deliveries - count,
                0,
            ),
            "metadata": {
                "version": "frequency_cap_v1"
            },
        }

    def record_delivery(
        self,
        *,
        user_id: str,
        channel: str,
        delivered_at: str | None = None,
    ) -> dict[str, Any]:
        item = {
            "delivery_id": str(uuid4()),
            "user_id": user_id,
            "channel": channel.lower(),
            "delivered_at": delivered_at or now_iso(),
        }
        self._delivery_log.append(item)
        return {
            "recorded": True,
            "delivery": deepcopy(item),
        }

    # RC223 — Provider health
    def calculate_provider_health(
        self,
        *,
        provider_id: str,
        success_count: int,
        failure_count: int,
        average_latency_ms: float,
    ) -> dict[str, Any]:
        total = max(success_count, 0) + max(
            failure_count,
            0,
        )
        success_rate = (
            success_count / total
            if total
            else 0.0
        )

        latency_penalty = min(
            max(average_latency_ms, 0) / 100,
            30,
        )

        score = max(
            0,
            min(
                100,
                success_rate * 100 - latency_penalty,
            ),
        )

        if score >= 90:
            status = "HEALTHY"
        elif score >= 70:
            status = "DEGRADED"
        else:
            status = "UNHEALTHY"

        result = {
            "provider_id": provider_id,
            "health_score": round(score, 2),
            "status": status,
            "success_rate": round(
                success_rate,
                4,
            ),
            "average_latency_ms": float(
                average_latency_ms
            ),
            "updated_at": now_iso(),
        }
        self._provider_health[
            provider_id
        ] = result
        return deepcopy(result)

    # RC224 — Provider fallback
    def select_provider_fallback(
        self,
        *,
        provider_ids: list[str],
        minimum_health_score: float = 70,
    ) -> dict[str, Any]:
        candidates = [
            self._provider_health[item]
            for item in provider_ids
            if item in self._provider_health
            and self._provider_health[item][
                "health_score"
            ] >= minimum_health_score
        ]

        candidates.sort(
            key=lambda item: (
                item["health_score"],
                -item["average_latency_ms"],
            ),
            reverse=True,
        )

        return {
            "selected": bool(candidates),
            "provider": (
                deepcopy(candidates[0])
                if candidates
                else None
            ),
            "candidate_count": len(candidates),
            "reason": (
                "HEALTHY_PROVIDER_SELECTED"
                if candidates
                else "NO_HEALTHY_PROVIDER"
            ),
        }

    # RC225 — Delivery SLA
    def evaluate_delivery_sla(
        self,
        *,
        created_at: str,
        delivered_at: str | None,
        target_seconds: int,
    ) -> dict[str, Any]:
        created = datetime.fromisoformat(created_at)

        if delivered_at is None:
            return {
                "met": False,
                "reason": "NOT_DELIVERED",
                "elapsed_seconds": None,
            }

        delivered = datetime.fromisoformat(
            delivered_at
        )
        elapsed = (
            delivered - created
        ).total_seconds()

        return {
            "met": elapsed <= target_seconds,
            "reason": (
                "SLA_MET"
                if elapsed <= target_seconds
                else "SLA_BREACHED"
            ),
            "elapsed_seconds": round(
                elapsed,
                3,
            ),
            "target_seconds": target_seconds,
        }

    # RC226 — Recommendation feedback
    def record_feedback(
        self,
        *,
        user_id: str,
        recommendation_id: str,
        feedback_type: str,
        comment: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        normalized = feedback_type.upper()

        if normalized not in {
            "HELPFUL",
            "NOT_HELPFUL",
            "WRONG_PRODUCT",
            "BAD_PRICE",
            "SPAM",
        }:
            return {
                "recorded": False,
                "reason": "INVALID_FEEDBACK_TYPE",
            }

        item = {
            "feedback_id": str(uuid4()),
            "user_id": user_id,
            "recommendation_id": recommendation_id,
            "feedback_type": normalized,
            "comment": comment,
            "metadata": metadata or {},
            "created_at": now_iso(),
        }
        self._feedback.append(item)

        return {
            "recorded": True,
            "feedback": deepcopy(item),
        }

    # RC227 — Recommendation acceptance
    def calculate_acceptance_metrics(
        self,
        *,
        recommendation_count: int,
        viewed_count: int,
        accepted_count: int,
    ) -> dict[str, Any]:
        recommendations = max(
            recommendation_count,
            0,
        )
        viewed = max(viewed_count, 0)
        accepted = max(accepted_count, 0)

        return {
            "view_rate": (
                round(viewed / recommendations, 4)
                if recommendations
                else 0.0
            ),
            "acceptance_rate": (
                round(accepted / viewed, 4)
                if viewed
                else 0.0
            ),
            "recommendation_count": recommendations,
            "viewed_count": viewed,
            "accepted_count": accepted,
        }

    # RC228 — False positive reporting
    def report_false_positive(
        self,
        *,
        user_id: str,
        deal_id: str,
        reason: str,
        observed_price: float | None = None,
    ) -> dict[str, Any]:
        return self.record_feedback(
            user_id=user_id,
            recommendation_id=deal_id,
            feedback_type="BAD_PRICE",
            comment=reason,
            metadata={
                "false_positive": True,
                "observed_price": observed_price,
            },
        )

    # RC229 — Trust score adjustment
    def adjust_source_trust(
        self,
        *,
        source_id: str,
        current_score: float,
        verified_successes: int,
        false_positive_count: int,
        complaint_count: int,
    ) -> dict[str, Any]:
        score = float(current_score)
        score += min(
            max(verified_successes, 0) * 0.5,
            10,
        )
        score -= min(
            max(false_positive_count, 0) * 5,
            40,
        )
        score -= min(
            max(complaint_count, 0) * 2,
            20,
        )
        score = round(
            min(max(score, 0), 100),
            2,
        )

        result = {
            "source_id": source_id,
            "trust_score": score,
            "updated_at": now_iso(),
        }
        self._trust_scores[
            source_id
        ] = result
        return deepcopy(result)

    # RC230 — Feedback analytics
    def summarize_feedback(
        self,
        *,
        recommendation_id: str | None = None,
    ) -> dict[str, Any]:
        items = list(self._feedback)

        if recommendation_id is not None:
            items = [
                item
                for item in items
                if item["recommendation_id"]
                == recommendation_id
            ]

        counts: dict[str, int] = {}

        for item in items:
            counts[item["feedback_type"]] = (
                counts.get(
                    item["feedback_type"],
                    0,
                )
                + 1
            )

        helpful = counts.get("HELPFUL", 0)
        not_helpful = sum(
            value
            for key, value in counts.items()
            if key != "HELPFUL"
        )

        total = helpful + not_helpful

        return {
            "feedback_count": len(items),
            "counts": counts,
            "helpfulness_rate": (
                round(helpful / total, 4)
                if total
                else 0.0
            ),
        }

    # RC231 — Watchlist budget policy
    def evaluate_budget_policy(
        self,
        *,
        effective_price: float,
        maximum_price: float,
        monthly_budget_remaining: float,
    ) -> dict[str, Any]:
        affordable = (
            effective_price <= maximum_price
            and effective_price
            <= monthly_budget_remaining
        )

        return {
            "eligible": affordable,
            "effective_price": effective_price,
            "maximum_price": maximum_price,
            "monthly_budget_remaining": (
                monthly_budget_remaining
            ),
            "reason": (
                "WITHIN_BUDGET"
                if affordable
                else "BUDGET_EXCEEDED"
            ),
        }

    # RC232 — Category quota
    def evaluate_category_quota(
        self,
        *,
        category: str,
        existing_count: int,
        maximum_count: int,
    ) -> dict[str, Any]:
        allowed = existing_count < maximum_count

        return {
            "category": category,
            "allowed": allowed,
            "existing_count": existing_count,
            "maximum_count": maximum_count,
            "remaining_count": max(
                maximum_count - existing_count,
                0,
            ),
        }

    # RC233 — Saved search
    def create_saved_search(
        self,
        *,
        user_id: str,
        name: str,
        filters: dict[str, Any],
    ) -> dict[str, Any]:
        search_id = str(uuid4())
        item = {
            "search_id": search_id,
            "user_id": user_id,
            "name": name,
            "filters": deepcopy(filters),
            "active": True,
            "created_at": now_iso(),
        }
        self._saved_searches[
            search_id
        ] = item
        return {
            "created": True,
            "saved_search": deepcopy(item),
        }

    def list_saved_searches(
        self,
        *,
        user_id: str,
    ) -> dict[str, Any]:
        items = [
            deepcopy(item)
            for item in self._saved_searches.values()
            if item["user_id"] == user_id
        ]
        return {
            "search_count": len(items),
            "searches": items,
        }

    # RC234 — Deal comparison
    def compare_deals(
        self,
        *,
        deals: list[dict[str, Any]],
    ) -> dict[str, Any]:
        compared = []

        for item in deals:
            effective_price = float(
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
            discount = float(
                item.get(
                    "observed_discount_pct",
                    0,
                )
            )

            comparison_score = (
                confidence * 0.55
                + discount * 0.35
                - effective_price * 0.0001
            )

            compared.append(
                {
                    **item,
                    "comparison_score": round(
                        comparison_score,
                        4,
                    ),
                }
            )

        compared.sort(
            key=lambda item: item[
                "comparison_score"
            ],
            reverse=True,
        )

        return {
            "deal_count": len(compared),
            "deals": compared,
            "best_deal": (
                compared[0]
                if compared
                else None
            ),
        }

    # RC235 — Purchase intent
    def record_purchase_intent(
        self,
        *,
        user_id: str,
        deal_id: str,
        intent_level: str,
    ) -> dict[str, Any]:
        normalized = intent_level.upper()

        if normalized not in {
            "LOW",
            "MEDIUM",
            "HIGH",
            "PURCHASED",
        }:
            return {
                "recorded": False,
                "reason": "INVALID_INTENT_LEVEL",
            }

        intent_id = str(uuid4())
        item = {
            "intent_id": intent_id,
            "user_id": user_id,
            "deal_id": deal_id,
            "intent_level": normalized,
            "created_at": now_iso(),
        }
        self._purchase_intents[
            intent_id
        ] = item
        return {
            "recorded": True,
            "intent": deepcopy(item),
        }

    # RC236 — Conversion attribution
    def attribute_conversion(
        self,
        *,
        user_id: str,
        deal_id: str,
        notification_id: str | None,
        order_value: float,
        affiliate_revenue: float = 0,
    ) -> dict[str, Any]:
        item = {
            "conversion_id": str(uuid4()),
            "user_id": user_id,
            "deal_id": deal_id,
            "notification_id": notification_id,
            "order_value": float(order_value),
            "affiliate_revenue": float(
                affiliate_revenue
            ),
            "created_at": now_iso(),
        }
        self._conversions.append(item)
        return {
            "attributed": True,
            "conversion": deepcopy(item),
        }

    # RC237 — Affiliate disclosure
    def build_affiliate_disclosure(
        self,
        *,
        affiliate_enabled: bool,
        commission_possible: bool,
    ) -> dict[str, Any]:
        if not affiliate_enabled:
            text = "Bu öneride affiliate bağlantısı kullanılmamaktadır."
        elif commission_possible:
            text = (
                "Bu bağlantı üzerinden yapılan satın alımdan "
                "komisyon kazanılabilir; öneri sıralaması bundan etkilenmez."
            )
        else:
            text = (
                "Affiliate bağlantısı kullanılabilir ancak bu işlemden "
                "komisyon kazanılmayabilir."
            )

        return {
            "required": affiliate_enabled,
            "disclosure": text,
            "ranking_independent": True,
        }

    # RC238 — Sponsored separation
    def validate_sponsored_separation(
        self,
        *,
        sponsored: bool,
        labeled_as_sponsored: bool,
        ranking_influenced: bool,
    ) -> dict[str, Any]:
        compliant = (
            (not sponsored)
            or (
                labeled_as_sponsored
                and not ranking_influenced
            )
        )

        return {
            "compliant": compliant,
            "issues": (
                []
                if compliant
                else [
                    "SPONSORED_CONTENT_NOT_SEPARATED"
                ]
            ),
        }

    # RC239 — Recommendation audit
    def audit_recommendation(
        self,
        *,
        recommendation_id: str,
        decision: str,
        evidence: dict[str, Any],
        affiliate_disclosure_present: bool,
        sponsored: bool,
        ranking_influenced: bool,
    ) -> dict[str, Any]:
        issues = []

        if not evidence:
            issues.append("MISSING_EVIDENCE")

        if decision == "BUY" and not evidence.get(
            "source_confidence"
        ):
            issues.append(
                "BUY_WITHOUT_SOURCE_CONFIDENCE"
            )

        if (
            sponsored
            and ranking_influenced
        ):
            issues.append(
                "SPONSORED_RANKING_INFLUENCE"
            )

        if (
            evidence.get("affiliate_enabled")
            and not affiliate_disclosure_present
        ):
            issues.append(
                "MISSING_AFFILIATE_DISCLOSURE"
            )

        report = {
            "audit_id": str(uuid4()),
            "recommendation_id": recommendation_id,
            "passed": len(issues) == 0,
            "issues": issues,
            "created_at": now_iso(),
        }
        self._recommendation_audits.append(
            report
        )
        return deepcopy(report)

    # RC240 — Consumer trust dashboard
    def build_trust_dashboard(
        self,
        *,
        recommendation_count: int,
        audited_count: int,
        passed_audit_count: int,
        feedback_count: int,
        helpful_feedback_count: int,
        false_positive_count: int,
        disclosure_compliance_pct: float,
    ) -> dict[str, Any]:
        audit_pass_rate = (
            passed_audit_count / audited_count
            if audited_count
            else 0.0
        )

        helpfulness_rate = (
            helpful_feedback_count / feedback_count
            if feedback_count
            else 0.0
        )

        false_positive_rate = (
            false_positive_count
            / recommendation_count
            if recommendation_count
            else 0.0
        )

        trust_score = (
            audit_pass_rate * 40
            + helpfulness_rate * 30
            + max(
                0,
                1 - false_positive_rate,
            ) * 20
            + min(
                max(
                    disclosure_compliance_pct,
                    0,
                ),
                100,
            )
            / 100
            * 10
        )

        if trust_score >= 90:
            status = "EXCELLENT"
        elif trust_score >= 75:
            status = "GOOD"
        elif trust_score >= 60:
            status = "NEEDS_IMPROVEMENT"
        else:
            status = "POOR"

        return {
            "trust_score": round(
                trust_score,
                2,
            ),
            "status": status,
            "audit_pass_rate": round(
                audit_pass_rate,
                4,
            ),
            "helpfulness_rate": round(
                helpfulness_rate,
                4,
            ),
            "false_positive_rate": round(
                false_positive_rate,
                4,
            ),
            "disclosure_compliance_pct": (
                disclosure_compliance_pct
            ),
            "metadata": {
                "version": "consumer_trust_dashboard_v1"
            },
        }
