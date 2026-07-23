from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from app.domains.ai_explanation.recommendation_explanation_service import (
    RecommendationExplanationService,
)
from app.domains.deal_intelligence.service import (
    DealIntelligenceService,
)
from app.domains.watchlist.watchlist_matcher import WatchlistMatcher


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class OpportunityRepository:
    def __init__(self) -> None:
        self._opportunities: dict[str, dict[str, Any]] = {}
        self._decisions: dict[str, list[dict[str, Any]]] = {}
        self._watchlist: dict[str, dict[str, Any]] = {}

    def save_opportunity(
        self,
        opportunity: dict[str, Any],
    ) -> dict[str, Any]:
        opportunity_id = opportunity.get(
            "opportunity_id"
        ) or str(uuid4())

        stored = {
            **opportunity,
            "opportunity_id": opportunity_id,
            "saved_at": opportunity.get(
                "saved_at"
            ) or now_iso(),
        }

        self._opportunities[
            opportunity_id
        ] = stored

        return deepcopy(stored)

    def get_opportunity(
        self,
        opportunity_id: str,
    ) -> dict[str, Any] | None:
        item = self._opportunities.get(
            opportunity_id
        )
        return deepcopy(item) if item else None

    def list_opportunities(
        self,
        *,
        product_key: str | None = None,
        source_id: str | None = None,
    ) -> list[dict[str, Any]]:
        items = list(
            self._opportunities.values()
        )

        if product_key is not None:
            items = [
                item
                for item in items
                if item.get(
                    "canonical_product_key"
                ) == product_key
            ]

        if source_id is not None:
            items = [
                item
                for item in items
                if item.get("source_id")
                == source_id
            ]

        return deepcopy(items)

    def append_decision(
        self,
        *,
        opportunity_id: str,
        decision: dict[str, Any],
    ) -> dict[str, Any]:
        record = {
            "decision_id": str(uuid4()),
            "opportunity_id": opportunity_id,
            "decision": deepcopy(decision),
            "created_at": now_iso(),
        }

        self._decisions.setdefault(
            opportunity_id,
            [],
        ).append(record)

        return deepcopy(record)

    def get_decision_history(
        self,
        opportunity_id: str,
    ) -> list[dict[str, Any]]:
        return deepcopy(
            self._decisions.get(
                opportunity_id,
                [],
            )
        )

    def add_watchlist_item(
        self,
        *,
        user_id: str,
        product_key: str,
        target_price: float | None = None,
        minimum_confidence: float = 60,
    ) -> dict[str, Any]:
        watch_id = str(uuid4())

        item = {
            "watch_id": watch_id,
            "user_id": user_id,
            "product_key": product_key,
            "target_price": target_price,
            "minimum_confidence": minimum_confidence,
            "active": True,
            "created_at": now_iso(),
        }

        self._watchlist[
            watch_id
        ] = item

        return deepcopy(item)

    def list_watchlist(
        self,
        *,
        user_id: str | None = None,
        active: bool | None = None,
    ) -> list[dict[str, Any]]:
        items = list(
            self._watchlist.values()
        )

        if user_id is not None:
            items = [
                item
                for item in items
                if item["user_id"] == user_id
            ]

        if active is not None:
            items = [
                item
                for item in items
                if item["active"] is active
            ]

        return deepcopy(items)


class DealAlertBridge:
    def build_alert(
        self,
        *,
        user_id: str,
        opportunity: dict[str, Any],
        recommendation: dict[str, Any],
    ) -> dict[str, Any]:
        decision = recommendation.get(
            "decision",
            "INSUFFICIENT_DATA",
        )
        confidence = float(
            recommendation.get(
                "confidence",
                0,
            )
        )

        should_alert = (
            decision == "BUY"
            and confidence >= 70
        )

        if confidence >= 85:
            alert_level = "URGENT"
        elif confidence >= 70:
            alert_level = "HIGH"
        elif confidence >= 50:
            alert_level = "MEDIUM"
        else:
            alert_level = "LOW"

        return {
            "alert_id": str(uuid4()),
            "user_id": user_id,
            "product_key": opportunity.get(
                "canonical_product_key"
            ),
            "opportunity_id": opportunity.get(
                "opportunity_id"
            ),
            "should_alert": should_alert,
            "alert_level": alert_level,
            "alert_score": confidence,
            "title": (
                "Güçlü fırsat tespit edildi"
                if should_alert
                else "Fırsat güncellendi"
            ),
            "message": recommendation.get(
                "summary",
                "",
            ),
            "channels": ["in_app"],
            "reasons": [
                recommendation.get(
                    "truth_status",
                    "UNKNOWN",
                )
            ],
            "metadata": {
                "bridge_version": "deal_alert_bridge_v1"
            },
        }


class DealDecisionOperationsService:
    def __init__(self) -> None:
        self.repository = OpportunityRepository()
        self.intelligence = DealIntelligenceService()
        self.explainer = RecommendationExplanationService()
        self.alert_bridge = DealAlertBridge()
        self.matcher = WatchlistMatcher()

    def evaluate_and_store(
        self,
        *,
        opportunities: list[dict[str, Any]],
        user_id: str | None = None,
    ) -> dict[str, Any]:
        intelligence_result = (
            self.intelligence.evaluate(
                opportunities=opportunities
            )
        )

        stored_opportunities = []

        for opportunity in intelligence_result[
            "ranking"
        ]["opportunities"]:
            stored_opportunities.append(
                self.repository.save_opportunity(
                    opportunity
                )
            )

        best = (
            stored_opportunities[0]
            if stored_opportunities
            else None
        )

        recommendation = intelligence_result.get(
            "recommendation"
        )

        explanation = (
            self.explainer.explain(
                recommendation=recommendation
            )
            if recommendation
            else None
        )

        decision_record = None
        alert = None
        watchlist_matches = {
            "match_count": 0,
            "matches": [],
        }

        if best and recommendation:
            decision_record = (
                self.repository.append_decision(
                    opportunity_id=best[
                        "opportunity_id"
                    ],
                    decision=recommendation,
                )
            )

            if user_id:
                alert = self.alert_bridge.build_alert(
                    user_id=user_id,
                    opportunity=best,
                    recommendation=recommendation,
                )

                watchlist_matches = (
                    self.matcher.match(
                        watch_items=self.repository.list_watchlist(
                            user_id=user_id,
                            active=True,
                        ),
                        opportunity=best,
                        recommendation=recommendation,
                    )
                )

        return {
            "stored_count": len(
                stored_opportunities
            ),
            "opportunities": stored_opportunities,
            "best_opportunity": best,
            "recommendation": recommendation,
            "explanation": explanation,
            "decision_record": decision_record,
            "alert": alert,
            "watchlist_matches": watchlist_matches,
            "metadata": {
                "operations_version": "deal_decision_operations_v1"
            },
        }
