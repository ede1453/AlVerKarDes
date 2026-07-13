from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timedelta, timezone
from statistics import mean
from typing import Any
from uuid import uuid4


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def now_iso() -> str:
    return now_utc().isoformat()


class GrowthRevenueIntelligenceService:
    def __init__(self) -> None:
        self._affiliate_clicks: list[dict[str, Any]] = []
        self._affiliate_conversions: list[dict[str, Any]] = []
        self._campaigns: dict[str, dict[str, Any]] = {}
        self._segments: dict[str, dict[str, Any]] = {}
        self._cohorts: dict[str, dict[str, Any]] = {}
        self._retailer_snapshots: list[dict[str, Any]] = []
        self._revenue_events: list[dict[str, Any]] = []
        self._experiments: dict[str, dict[str, Any]] = {}
        self._growth_events: list[dict[str, Any]] = []

    # RC261
    def calculate_customer_acquisition_cost(
        self,
        *,
        marketing_spend: float,
        acquired_users: int,
    ) -> dict[str, Any]:
        cac = (
            float(marketing_spend) / acquired_users
            if acquired_users > 0
            else 0.0
        )
        return {
            "cac": round(cac, 2),
            "marketing_spend": float(marketing_spend),
            "acquired_users": acquired_users,
        }

    # RC262
    def calculate_lifetime_value(
        self,
        *,
        average_order_value: float,
        purchase_frequency_per_year: float,
        gross_margin_pct: float,
        retention_years: float,
    ) -> dict[str, Any]:
        ltv = (
            average_order_value
            * purchase_frequency_per_year
            * (gross_margin_pct / 100)
            * retention_years
        )
        return {
            "ltv": round(ltv, 2),
            "metadata": {"version": "ltv_v1"},
        }

    # RC263
    def calculate_ltv_cac_ratio(
        self,
        *,
        ltv: float,
        cac: float,
    ) -> dict[str, Any]:
        ratio = ltv / cac if cac > 0 else 0.0
        if ratio >= 3:
            status = "HEALTHY"
        elif ratio >= 1:
            status = "WATCH"
        else:
            status = "UNHEALTHY"
        return {
            "ltv_cac_ratio": round(ratio, 2),
            "status": status,
        }

    # RC264
    def calculate_monthly_active_users(
        self,
        *,
        user_activity: list[dict[str, Any]],
        reference_time: str,
    ) -> dict[str, Any]:
        reference = datetime.fromisoformat(reference_time)
        cutoff = reference - timedelta(days=30)
        users = {
            item["user_id"]
            for item in user_activity
            if datetime.fromisoformat(item["occurred_at"]) >= cutoff
        }
        return {
            "monthly_active_users": len(users),
            "user_ids": sorted(users),
        }

    # RC265
    def calculate_daily_active_users(
        self,
        *,
        user_activity: list[dict[str, Any]],
        reference_time: str,
    ) -> dict[str, Any]:
        reference = datetime.fromisoformat(reference_time)
        cutoff = reference - timedelta(days=1)
        users = {
            item["user_id"]
            for item in user_activity
            if datetime.fromisoformat(item["occurred_at"]) >= cutoff
        }
        return {
            "daily_active_users": len(users),
            "user_ids": sorted(users),
        }

    # RC266
    def calculate_stickiness(
        self,
        *,
        daily_active_users: int,
        monthly_active_users: int,
    ) -> dict[str, Any]:
        ratio = (
            daily_active_users / monthly_active_users
            if monthly_active_users > 0
            else 0.0
        )
        return {
            "stickiness": round(ratio, 4),
            "stickiness_pct": round(ratio * 100, 2),
        }

    # RC267
    def calculate_activation_rate(
        self,
        *,
        registered_users: int,
        activated_users: int,
    ) -> dict[str, Any]:
        rate = (
            activated_users / registered_users
            if registered_users > 0
            else 0.0
        )
        return {
            "activation_rate": round(rate, 4),
            "activation_pct": round(rate * 100, 2),
        }

    # RC268
    def calculate_retention_rate(
        self,
        *,
        cohort_size: int,
        retained_users: int,
    ) -> dict[str, Any]:
        rate = (
            retained_users / cohort_size
            if cohort_size > 0
            else 0.0
        )
        return {
            "retention_rate": round(rate, 4),
            "retention_pct": round(rate * 100, 2),
        }

    # RC269
    def calculate_churn_rate(
        self,
        *,
        starting_users: int,
        churned_users: int,
    ) -> dict[str, Any]:
        rate = (
            churned_users / starting_users
            if starting_users > 0
            else 0.0
        )
        return {
            "churn_rate": round(rate, 4),
            "churn_pct": round(rate * 100, 2),
        }

    # RC270
    def build_growth_funnel(
        self,
        *,
        visitors: int,
        registrations: int,
        activations: int,
        alerts_created: int,
        purchases: int,
    ) -> dict[str, Any]:
        def rate(a: int, b: int) -> float:
            return round(a / b, 4) if b > 0 else 0.0

        return {
            "visitors": visitors,
            "registrations": registrations,
            "activations": activations,
            "alerts_created": alerts_created,
            "purchases": purchases,
            "visitor_to_registration": rate(registrations, visitors),
            "registration_to_activation": rate(activations, registrations),
            "activation_to_alert": rate(alerts_created, activations),
            "alert_to_purchase": rate(purchases, alerts_created),
        }

    # RC271
    def record_affiliate_click(
        self,
        *,
        user_id: str,
        deal_id: str,
        retailer_id: str,
        campaign_id: str | None = None,
    ) -> dict[str, Any]:
        item = {
            "click_id": str(uuid4()),
            "user_id": user_id,
            "deal_id": deal_id,
            "retailer_id": retailer_id,
            "campaign_id": campaign_id,
            "clicked_at": now_iso(),
        }
        self._affiliate_clicks.append(item)
        return {"recorded": True, "click": deepcopy(item)}

    # RC272
    def record_affiliate_conversion(
        self,
        *,
        click_id: str,
        order_value: float,
        commission_value: float,
    ) -> dict[str, Any]:
        click = next(
            (item for item in self._affiliate_clicks if item["click_id"] == click_id),
            None,
        )
        if click is None:
            return {"recorded": False, "reason": "CLICK_NOT_FOUND"}

        conversion = {
            "conversion_id": str(uuid4()),
            "click_id": click_id,
            "user_id": click["user_id"],
            "deal_id": click["deal_id"],
            "retailer_id": click["retailer_id"],
            "order_value": float(order_value),
            "commission_value": float(commission_value),
            "converted_at": now_iso(),
        }
        self._affiliate_conversions.append(conversion)
        return {"recorded": True, "conversion": deepcopy(conversion)}

    # RC273
    def calculate_affiliate_conversion_rate(self) -> dict[str, Any]:
        click_count = len(self._affiliate_clicks)
        conversion_count = len(self._affiliate_conversions)
        rate = conversion_count / click_count if click_count else 0.0
        return {
            "click_count": click_count,
            "conversion_count": conversion_count,
            "conversion_rate": round(rate, 4),
        }

    # RC274
    def calculate_revenue_per_click(self) -> dict[str, Any]:
        clicks = len(self._affiliate_clicks)
        revenue = sum(item["commission_value"] for item in self._affiliate_conversions)
        return {
            "revenue_per_click": round(revenue / clicks, 4) if clicks else 0.0,
            "total_revenue": round(revenue, 2),
        }

    # RC275
    def calculate_revenue_per_user(self) -> dict[str, Any]:
        users = {item["user_id"] for item in self._affiliate_clicks}
        revenue = sum(item["commission_value"] for item in self._affiliate_conversions)
        return {
            "revenue_per_user": round(revenue / len(users), 2) if users else 0.0,
            "user_count": len(users),
        }

    # RC276
    def evaluate_revenue_independence(
        self,
        *,
        recommendation_score: float,
        commission_rate: float,
        ranking_changed: bool,
    ) -> dict[str, Any]:
        compliant = not ranking_changed
        return {
            "compliant": compliant,
            "recommendation_score": recommendation_score,
            "commission_rate": commission_rate,
            "issues": [] if compliant else ["REVENUE_INFLUENCED_RANKING"],
        }

    # RC277
    def create_campaign(
        self,
        *,
        campaign_id: str,
        name: str,
        budget: float,
        starts_at: str,
        ends_at: str,
    ) -> dict[str, Any]:
        campaign = {
            "campaign_id": campaign_id,
            "name": name,
            "budget": float(budget),
            "spent": 0.0,
            "starts_at": starts_at,
            "ends_at": ends_at,
            "status": "ACTIVE",
        }
        self._campaigns[campaign_id] = campaign
        return {"created": True, "campaign": deepcopy(campaign)}

    # RC278
    def record_campaign_spend(
        self,
        *,
        campaign_id: str,
        amount: float,
    ) -> dict[str, Any]:
        campaign = self._campaigns.get(campaign_id)
        if campaign is None:
            return {"recorded": False, "reason": "CAMPAIGN_NOT_FOUND"}

        campaign["spent"] = round(campaign["spent"] + amount, 2)
        if campaign["spent"] >= campaign["budget"]:
            campaign["status"] = "BUDGET_EXHAUSTED"

        return {"recorded": True, "campaign": deepcopy(campaign)}

    # RC279
    def calculate_campaign_roi(
        self,
        *,
        campaign_id: str,
        attributed_revenue: float,
    ) -> dict[str, Any]:
        campaign = self._campaigns.get(campaign_id)
        if campaign is None:
            return {"calculated": False, "reason": "CAMPAIGN_NOT_FOUND"}

        spend = campaign["spent"]
        roi = ((attributed_revenue - spend) / spend) if spend > 0 else 0.0
        return {
            "calculated": True,
            "campaign_id": campaign_id,
            "roi": round(roi, 4),
            "roi_pct": round(roi * 100, 2),
        }

    # RC280
    def evaluate_campaign_budget(
        self,
        *,
        campaign_id: str,
        requested_amount: float,
    ) -> dict[str, Any]:
        campaign = self._campaigns.get(campaign_id)
        if campaign is None:
            return {"allowed": False, "reason": "CAMPAIGN_NOT_FOUND"}

        remaining = campaign["budget"] - campaign["spent"]
        return {
            "allowed": requested_amount <= remaining,
            "remaining_budget": round(max(remaining, 0), 2),
        }

    # RC281
    def create_user_segment(
        self,
        *,
        segment_id: str,
        name: str,
        rules: dict[str, Any],
    ) -> dict[str, Any]:
        segment = {
            "segment_id": segment_id,
            "name": name,
            "rules": deepcopy(rules),
            "created_at": now_iso(),
        }
        self._segments[segment_id] = segment
        return {"created": True, "segment": deepcopy(segment)}

    # RC282
    def evaluate_segment_membership(
        self,
        *,
        segment_id: str,
        user_features: dict[str, Any],
    ) -> dict[str, Any]:
        segment = self._segments.get(segment_id)
        if segment is None:
            return {"member": False, "reason": "SEGMENT_NOT_FOUND"}

        rules = segment["rules"]
        member = True

        for key, expected in rules.items():
            actual = user_features.get(key)
            if isinstance(expected, dict):
                minimum = expected.get("min")
                maximum = expected.get("max")
                if minimum is not None and (actual is None or actual < minimum):
                    member = False
                if maximum is not None and (actual is None or actual > maximum):
                    member = False
            elif actual != expected:
                member = False

        return {"member": member, "segment_id": segment_id}

    # RC283
    def build_behavioral_segment(
        self,
        *,
        user_id: str,
        purchase_count: int,
        alert_count: int,
        open_rate: float,
    ) -> dict[str, Any]:
        if purchase_count >= 5:
            segment = "POWER_BUYER"
        elif alert_count >= 10 and open_rate >= 0.5:
            segment = "ACTIVE_DEAL_HUNTER"
        elif alert_count >= 5:
            segment = "PASSIVE_WATCHER"
        else:
            segment = "NEW_OR_LOW_ACTIVITY"

        return {
            "user_id": user_id,
            "behavioral_segment": segment,
        }

    # RC284
    def create_cohort(
        self,
        *,
        cohort_id: str,
        user_ids: list[str],
        started_at: str,
    ) -> dict[str, Any]:
        cohort = {
            "cohort_id": cohort_id,
            "user_ids": sorted(set(user_ids)),
            "started_at": started_at,
        }
        self._cohorts[cohort_id] = cohort
        return {"created": True, "cohort": deepcopy(cohort)}

    # RC285
    def calculate_cohort_retention(
        self,
        *,
        cohort_id: str,
        active_user_ids: list[str],
    ) -> dict[str, Any]:
        cohort = self._cohorts.get(cohort_id)
        if cohort is None:
            return {"calculated": False, "reason": "COHORT_NOT_FOUND"}

        base = set(cohort["user_ids"])
        active = base.intersection(active_user_ids)
        rate = len(active) / len(base) if base else 0.0

        return {
            "calculated": True,
            "cohort_id": cohort_id,
            "retained_users": len(active),
            "retention_rate": round(rate, 4),
        }

    # RC286
    def calculate_reactivation_rate(
        self,
        *,
        inactive_users: int,
        reactivated_users: int,
    ) -> dict[str, Any]:
        rate = reactivated_users / inactive_users if inactive_users > 0 else 0.0
        return {"reactivation_rate": round(rate, 4)}

    # RC287
    def record_retailer_snapshot(
        self,
        *,
        retailer_id: str,
        offer_count: int,
        valid_offer_count: int,
        average_discount_pct: float,
        conversion_count: int,
    ) -> dict[str, Any]:
        item = {
            "snapshot_id": str(uuid4()),
            "retailer_id": retailer_id,
            "offer_count": offer_count,
            "valid_offer_count": valid_offer_count,
            "average_discount_pct": float(average_discount_pct),
            "conversion_count": conversion_count,
            "created_at": now_iso(),
        }
        self._retailer_snapshots.append(item)
        return {"recorded": True, "snapshot": deepcopy(item)}

    # RC288
    def calculate_retailer_quality(
        self,
        *,
        offer_count: int,
        valid_offer_count: int,
        false_positive_count: int,
    ) -> dict[str, Any]:
        validity = valid_offer_count / offer_count if offer_count > 0 else 0.0
        penalty = min(false_positive_count * 0.05, 0.5)
        score = max(0.0, validity - penalty) * 100

        return {
            "retailer_quality_score": round(score, 2),
            "validity_rate": round(validity, 4),
        }

    # RC289
    def calculate_retailer_conversion(
        self,
        *,
        click_count: int,
        conversion_count: int,
    ) -> dict[str, Any]:
        rate = conversion_count / click_count if click_count > 0 else 0.0
        return {"retailer_conversion_rate": round(rate, 4)}

    # RC290
    def build_retailer_scorecard(
        self,
        *,
        retailer_id: str,
        quality_score: float,
        conversion_rate: float,
        average_discount_pct: float,
        trust_score: float,
    ) -> dict[str, Any]:
        score = (
            quality_score * 0.35
            + conversion_rate * 100 * 0.20
            + min(average_discount_pct, 100) * 0.20
            + trust_score * 0.25
        )

        return {
            "retailer_id": retailer_id,
            "score": round(min(max(score, 0), 100), 2),
        }

    # RC291
    def create_growth_experiment(
        self,
        *,
        experiment_id: str,
        variants: list[str],
        target_metric: str,
    ) -> dict[str, Any]:
        cleaned = sorted({str(v).strip() for v in variants if str(v).strip()})
        if len(cleaned) < 2:
            return {"created": False, "reason": "TWO_VARIANTS_REQUIRED"}

        experiment = {
            "experiment_id": experiment_id,
            "variants": cleaned,
            "target_metric": target_metric,
            "results": {variant: [] for variant in cleaned},
        }
        self._experiments[experiment_id] = experiment
        return {"created": True, "experiment": deepcopy(experiment)}

    # RC292
    def record_experiment_result(
        self,
        *,
        experiment_id: str,
        variant: str,
        metric_value: float,
    ) -> dict[str, Any]:
        experiment = self._experiments.get(experiment_id)
        if experiment is None:
            return {"recorded": False, "reason": "EXPERIMENT_NOT_FOUND"}
        if variant not in experiment["results"]:
            return {"recorded": False, "reason": "VARIANT_NOT_FOUND"}

        experiment["results"][variant].append(float(metric_value))
        return {"recorded": True}

    # RC293
    def evaluate_experiment(
        self,
        *,
        experiment_id: str,
    ) -> dict[str, Any]:
        experiment = self._experiments.get(experiment_id)
        if experiment is None:
            return {"evaluated": False, "reason": "EXPERIMENT_NOT_FOUND"}

        averages = {
            variant: round(mean(values), 4) if values else 0.0
            for variant, values in experiment["results"].items()
        }
        winner = max(averages, key=averages.get) if averages else None

        return {
            "evaluated": True,
            "averages": averages,
            "winner": winner,
        }

    # RC294
    def record_growth_event(
        self,
        *,
        user_id: str,
        event_type: str,
        value: float = 1,
    ) -> dict[str, Any]:
        item = {
            "event_id": str(uuid4()),
            "user_id": user_id,
            "event_type": event_type.upper(),
            "value": float(value),
            "created_at": now_iso(),
        }
        self._growth_events.append(item)
        return {"recorded": True, "event": deepcopy(item)}

    # RC295
    def calculate_north_star_metric(
        self,
        *,
        qualified_deal_views: int,
        accepted_recommendations: int,
        purchases: int,
    ) -> dict[str, Any]:
        value = (
            qualified_deal_views * 0.2
            + accepted_recommendations * 0.3
            + purchases * 0.5
        )
        return {"north_star_value": round(value, 2)}

    # RC296
    def calculate_gross_merchandise_value(
        self,
        *,
        order_values: list[float],
    ) -> dict[str, Any]:
        gmv = sum(float(x) for x in order_values)
        return {
            "gmv": round(gmv, 2),
            "order_count": len(order_values),
        }

    # RC297
    def calculate_take_rate(
        self,
        *,
        revenue: float,
        gmv: float,
    ) -> dict[str, Any]:
        rate = revenue / gmv if gmv > 0 else 0.0
        return {
            "take_rate": round(rate, 4),
            "take_rate_pct": round(rate * 100, 2),
        }

    # RC298
    def calculate_revenue_quality(
        self,
        *,
        total_revenue: float,
        disclosed_revenue: float,
        trust_compliant_revenue: float,
    ) -> dict[str, Any]:
        disclosed_rate = disclosed_revenue / total_revenue if total_revenue > 0 else 0.0
        compliant_rate = (
            trust_compliant_revenue / total_revenue
            if total_revenue > 0
            else 0.0
        )
        score = (disclosed_rate * 0.5 + compliant_rate * 0.5) * 100

        return {
            "revenue_quality_score": round(score, 2),
            "disclosed_rate": round(disclosed_rate, 4),
            "trust_compliant_rate": round(compliant_rate, 4),
        }

    # RC299
    def build_growth_health_report(
        self,
        *,
        activation_rate: float,
        retention_rate: float,
        churn_rate: float,
        ltv_cac_ratio: float,
        revenue_quality_score: float,
    ) -> dict[str, Any]:
        score = (
            activation_rate * 100 * 0.20
            + retention_rate * 100 * 0.25
            + max(0, 1 - churn_rate) * 100 * 0.20
            + min(ltv_cac_ratio / 3, 1) * 100 * 0.20
            + revenue_quality_score * 0.15
        )

        if score >= 85:
            status = "EXCELLENT"
        elif score >= 70:
            status = "HEALTHY"
        elif score >= 50:
            status = "WATCH"
        else:
            status = "UNHEALTHY"

        return {
            "growth_health_score": round(score, 2),
            "status": status,
        }

    # RC300
    def build_executive_dashboard(
        self,
        *,
        mau: int,
        dau: int,
        activation_rate: float,
        retention_rate: float,
        churn_rate: float,
        gmv: float,
        revenue: float,
        trust_score: float,
        growth_health_score: float,
    ) -> dict[str, Any]:
        return {
            "mau": mau,
            "dau": dau,
            "stickiness": round(dau / mau, 4) if mau > 0 else 0.0,
            "activation_rate": activation_rate,
            "retention_rate": retention_rate,
            "churn_rate": churn_rate,
            "gmv": gmv,
            "revenue": revenue,
            "take_rate": round(revenue / gmv, 4) if gmv > 0 else 0.0,
            "trust_score": trust_score,
            "growth_health_score": growth_health_score,
            "generated_at": now_iso(),
            "metadata": {"version": "executive_dashboard_v1"},
        }
